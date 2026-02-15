# LLM
import re
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import time

COMPARATIVE_KEYWORDS = re.compile(
    r'\b(compare|comparison|contrast|difference|differences|differ|versus|vs\.?|'
    r'both|all documents|all files|each document|each file|'
    r'summarize all|summarize both|across|between the|similarities)\b',
    re.IGNORECASE
)

class LLMService:
    def __init__(self, groq_api_key):
        self.groq_api_key = groq_api_key

        self.model = "llama-3.1-8b-instant"

        # Initialize Groq LLM
        self.Table_Checker = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name=self.model, max_tokens=1)
        self.Table_Extractor = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name=self.model)
        self.Chat = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name=self.model)

    # Function to filter and extract information from tables
    def extract_info_from_table(self, table):

        prompt_template = ChatPromptTemplate.from_messages([
            ("user", "{table}\n\nAnalyze the above table and tell me whether it is a proper table or no. Just return 'True' or 'False' based on you decision. I want no other output.")
        ])

        chain = prompt_template | self.Table_Checker | StrOutputParser()
        extracted_text = chain.invoke({"table": table})

        good_table = True if 'True' in extracted_text else False

        if not good_table:
            return

        # Define a prompt template for table summarization
        prompt_template = ChatPromptTemplate.from_messages([
            ("user", "{table}\n\nRead the above table and get each of its records in proper serialized format.")
        ])

        # Run LLM on the table data
        chain = prompt_template | self.Table_Extractor | StrOutputParser()
        extracted_text = chain.invoke({"table": table})

        return extracted_text

    def _is_comparative_query(self, question):
        return bool(COMPARATIVE_KEYWORDS.search(question))

    # Function to run RAG-based QA
    def ask_question(self, vector_db, question):
        is_comparative = self._is_comparative_query(question)
        k = 20 if is_comparative else 8

        # Manually handle retrieval to track latency
        retriever = vector_db.as_retriever(search_kwargs={"k": k})

        start_retrieval = time.time()
        docs = retriever.invoke(question)
        retrieval_time = time.time() - start_retrieval

        # For comparative queries, ensure chunks from multiple sources are included
        if is_comparative and docs:
            sources = {}
            for doc in docs:
                src = doc.metadata.get("source", "unknown")
                sources.setdefault(src, []).append(doc)
            # If we have multiple sources, take top chunks from each source evenly
            if len(sources) > 1:
                per_source = max(4, k // len(sources))
                balanced_docs = []
                for src_docs in sources.values():
                    balanced_docs.extend(src_docs[:per_source])
                docs = balanced_docs

        # Build context from retrieved documents
        context = "\n\n".join(doc.page_content for doc in docs)

        if is_comparative:
            system_msg = (
                "Use the following context to answer the question. The context contains information from multiple documents. "
                "Compare and contrast information across all documents. If you don't know the answer, say you don't know.\n\nContext:\n{context}"
            )
        else:
            system_msg = "Use the following context to answer the question. If you don't know the answer, say you don't know.\n\nContext:\n{context}"

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            ("user", "{question}")
        ])

        chain = prompt | self.Chat
        response = chain.invoke({"context": context, "question": question})

        # Extract token usage from Groq response metadata
        usage = response.response_metadata.get("token_usage", {})
        tokens_input = usage.get("prompt_tokens", 0)
        tokens_output = usage.get("completion_tokens", 0)

        return {
            'result': response.content,
            'source_documents': docs,
            'retrieval_time': retrieval_time,
            'chunks_count': len(docs),
            'tokens_input': tokens_input,
            'tokens_output': tokens_output
        }
