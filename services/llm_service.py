# LLM
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.chains import RetrievalQA

class LLMService:
    def __init__(self, groq_api_key):
        self.groq_api_key = groq_api_key

        self.model = "gemma2-9b-it"

        # Initialize Groq LLM (using Mixtral for best performance)
        self.Table_Checker = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name=self.model, max_tokens=1)
        self.Table_Extractor = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name=self.model)
        self.Chat = ChatGroq(temperature=0, groq_api_key=groq_api_key, model_name=self.model)

    # Function to filter and extract information from tables
    def extract_info_from_table(self, table):

        prompt_template = ChatPromptTemplate(
            input_variables=["table"],
            messages=[
                {"role": "user", "content": "{table}\n\nAnalyze the above table and tell me whether it is a proper table or no. Just return 'True' or 'False' based on you decision. I want no other output."}
            ]
        )

        llm_chain = LLMChain(llm=self.Table_Checker, prompt=prompt_template)
        extracted_text = llm_chain.run(table=table)

        good_table = True if 'True' in extracted_text else False

        if not good_table:
            return

        # Define a prompt template for table summarization
        prompt_template = ChatPromptTemplate(
            input_variables=["table"],
            messages=[
                {"role": "user", "content": "{table}\n\nRead the above table and get each of its records in proper serialized format."}
            ]
        )

        # Run LLM on the table data
        llm_chain = LLMChain(llm=self.Table_Extractor, prompt=prompt_template)
        extracted_text = llm_chain.run(table=table)

        return extracted_text

    # Function to run RAG-based QA
    def ask_question(self, vector_db, question):
        retriever = vector_db.as_retriever()
        qa_chain = RetrievalQA.from_chain_type(llm=self.Chat, retriever=retriever)
        response = qa_chain.invoke(question)
        return response