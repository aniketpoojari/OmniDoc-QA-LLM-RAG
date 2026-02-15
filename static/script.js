// static/js/script.js

$(document).ready(function() {
    // Document type selector
    $('#docTypeSelector').change(function() {
        const selected = $(this).val();
        if (selected === 'PDF') {
            $('#pdfUploader').show();
            $('#websiteUploader').hide();
        } else {
            $('#pdfUploader').hide();
            $('#websiteUploader').show();
        }
    });
    
    // PDF Upload
    $('#pdfForm').submit(function(e) {
        e.preventDefault();
        const fileInput = $('#pdfFile')[0];
        
        if (fileInput.files.length === 0) {
            showStatus('#pdfUploadStatus', 'Please select a PDF file.', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        showStatus('#pdfUploadStatus', '<div class="spinner"></div> Uploading and processing PDF...', 'loading');
        
        $.ajax({
            url: '/upload_pdf',
            type: 'POST',
            data: formData,
            contentType: false,
            processData: false,
            success: function(response) {
                if (response.status === 'success') {
                    showStatus('#pdfUploadStatus', response.message, 'success');
                    addDocumentToList(response.document);
                    $('#pdfFile').val(''); // Reset file input
                    enableChatInput();
                } else {
                    showStatus('#pdfUploadStatus', response.message, 'error');
                }
            },
            error: function() {
                showStatus('#pdfUploadStatus', 'An error occurred during upload.', 'error');
            }
        });
    });
    
    // Process Website
    $('#processWebsiteBtn').click(function() {
        const url = $('#websiteUrl').val().trim();
        
        if (!url) {
            showStatus('#websiteProcessStatus', 'Please enter a website URL.', 'error');
            return;
        }
        
        showStatus('#websiteProcessStatus', '<div class="spinner"></div> Processing website...', 'loading');
        
        $.ajax({
            url: '/process_website',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ url: url }),
            success: function(response) {
                if (response.status === 'success') {
                    showStatus('#websiteProcessStatus', response.message, 'success');
                    addDocumentToList(response.document);
                    $('#websiteUrl').val(''); // Reset URL input
                    enableChatInput();
                } else {
                    showStatus('#websiteProcessStatus', response.message, 'error');
                }
            },
            error: function() {
                showStatus('#websiteProcessStatus', 'An error occurred while processing the website.', 'error');
            }
        });
    });
    
    // Delete document handler
    $(document).on('click', '.delete-btn', function() {
        const docId = $(this).data('id');
        
        $.ajax({
            url: '/delete_document',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ id: docId }),
            success: function(response) {
                if (response.status === 'success') {
                    $(`.document-item[data-id="${docId}"]`).remove();
                    
                    // Check if there are any documents left
                    if ($('.document-item').length === 0) {
                        $('#documentsList').html('<div class="no-docs text-muted fst-italic text-center py-3"><i class="bi bi-info-circle"></i> No documents uploaded yet</div>');
                        disableChatInput();
                    }
                }
            }
        });
    });
    
    // Ask button handler
    $('#askButton').click(function() {
        sendQuestion();
    });
    
    // Enter key in text area
    $('#questionInput').keydown(function(e) {
        if (e.keyCode === 13 && !e.shiftKey) {
            e.preventDefault();
            sendQuestion();
        }
    });
    
    // Clear chat history
    $('#clearChat').click(function() {
        $.ajax({
            url: '/clear_chat',
            type: 'POST',
            success: function(response) {
                if (response.status === 'success') {
                    $('#chatHistory').html('<div class="no-chat text-muted fst-italic text-center py-5"><i class="bi bi-chat-dots"></i><p>Ask questions about your documents to start a conversation</p></div>');
                }
            }
        });
    });
    
    // Function to send question
    function sendQuestion() {
        const question = $('#questionInput').val().trim();
        
        if (!question) {
            return;
        }
        
        // Add user message to chat
        addMessageToChat('user', question);
        
        // Clear input
        $('#questionInput').val('');
        
        // Show loading
        showStatus('#chatStatus', '<div class="spinner"></div> Searching...', 'loading');
        
        // Disable ask button
        $('#askButton').prop('disabled', true);
        
        // Send request
        $.ajax({
            url: '/ask_question',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ question: question }),
            success: function(response) {
                if (response.status === 'success') {
                    // Add assistant message to chat
                    addMessageToChat('assistant', response.response, response.metrics, response.query_id);
                    
                    // Clear status
                    $('#chatStatus').html('');
                } else {
                    showStatus('#chatStatus', response.message, 'error');
                }
                
                // Re-enable ask button
                $('#askButton').prop('disabled', false);
            },
            error: function() {
                showStatus('#chatStatus', 'An error occurred while processing your question.', 'error');
                $('#askButton').prop('disabled', false);
            }
        });
    }
    
    // Function to add message to chat
    function addMessageToChat(role, content, metrics, queryId) {
        // Remove no-chat message if present
        $('.no-chat').remove();
        
        let messageHTML = '';
        
        if (role === 'user') {
            const sanitizedContent = DOMPurify.sanitize(content); // Clean user input
            messageHTML = `
                <div class="message user-message mb-3">
                    <div class="d-flex align-items-center mb-1">
                        <div class="user-avatar bg-primary text-white rounded-circle me-2">
                            <i class="bi bi-person-fill"></i>
                        </div>
                        <strong>You</strong>
                    </div>
                    <div class="message-content">
                        ${sanitizedContent}
                    </div>
                </div>
            `;
        } else {
            let metricsHTML = '';
            if (metrics) {
                metricsHTML = `
                    <div class="metrics-row mt-1">
                        <span><i class="bi bi-clock"></i> ${metrics.latency}s</span>
                        <span><i class="bi bi-database"></i> ${metrics.chunks_count} chunks</span>
                        <span><i class="bi bi-arrow-right-circle"></i> ${metrics.tokens_input} in</span>
                        <span><i class="bi bi-arrow-left-circle"></i> ${metrics.tokens_output} out</span>
                    </div>
                `;
            }
            messageHTML = `
                <div class="message assistant-message mb-3">
                    <div class="d-flex align-items-center mb-1">
                        <div class="assistant-avatar bg-success text-white rounded-circle me-2">
                            <i class="bi bi-robot"></i>
                        </div>
                        <strong>Assistant</strong>
                    </div>
                    <div class="message-content">
                        ${content}
                    </div>
                    ${metricsHTML}
                    <div class="feedback-buttons mt-2">
                        <button class="btn btn-sm btn-outline-success feedback-btn" data-relevant="true" data-query-id="${queryId}">
                            <i class="bi bi-hand-thumbs-up"></i>
                        </button>
                        <button class="btn btn-sm btn-outline-danger feedback-btn" data-relevant="false" data-query-id="${queryId}">
                            <i class="bi bi-hand-thumbs-down"></i>
                        </button>
                    </div>
                </div>
            `;
        }
        
        $('#chatHistory').append(messageHTML);
        
        // Scroll to bottom
        $('#chatHistory').scrollTop($('#chatHistory')[0].scrollHeight);
    }

    // Feedback button handler
    $(document).on('click', '.feedback-btn', function() {
        const isRelevant = $(this).data('relevant');
        const queryId = $(this).data('query-id');
        const $btn = $(this);
        const $btnContainer = $btn.parent();

        $.ajax({
            url: '/feedback',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ query_id: queryId, relevant: isRelevant }),
            success: function(response) {
                if (response.status === 'success') {
                    // Reset all buttons in this group
                    $btnContainer.find('.feedback-btn').removeClass('active btn-success btn-danger')
                        .addClass(function() {
                            return $(this).data('relevant') ? 'btn-outline-success' : 'btn-outline-danger';
                        });
                    // Highlight selected button
                    if (isRelevant) {
                        $btn.removeClass('btn-outline-success').addClass('active btn-success');
                    } else {
                        $btn.removeClass('btn-outline-danger').addClass('active btn-danger');
                    }
                }
            }
        });
    });
    
    // Function to add document to list
    function addDocumentToList(doc) {
        // Remove no-docs message if present
        $('.no-docs').remove();
        
        // const docHTML = `
        //     <div class="document-item card mb-2" data-id="${doc.id}">
        //         <div class="card-body py-2 px-3">
        //             <div class="d-flex justify-content-between align-items-center">
        //                 <div>
        //                     <span class="badge bg-info me-2">${doc.type}</span>
        //                     <span class="text-truncate">${doc.name}</span>
        //                 </div>
        //                 <button class="btn btn-sm btn-danger delete-btn" data-id="${doc.id}">
        //                     <i class="bi bi-trash"></i>
        //                 </button>
        //             </div>
        //         </div>
        //     </div>
        // `;

        const docHTML = `
            <div class="document-item card mb-2" data-id="${doc.id}">
                <div class="card-body py-2 px-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center overflow-hidden">
                            <span class="badge bg-info me-2 flex-shrink-0">${doc.type}</span>
                            <span class="text-truncate">${doc.name}</span>
                        </div>
                        <button class="btn btn-sm btn-danger delete-btn flex-shrink-0" data-id="${doc.id}">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        $('#documentsList').append(docHTML);
    }
    
    // Function to show status messages
    function showStatus(selector, message, type) {
        const statusClass = type === 'error' ? 'status-error' : 
                          type === 'success' ? 'status-success' : 'status-loading';
        
        $(selector).html(`<div class="${statusClass}">${message}</div>`);
        
        if (type === 'success') {
            // Clear success message after 3 seconds
            setTimeout(function() {
                $(selector).html('');
            }, 3000);
        }
    }
    
    // Enable/disable chat input
    function enableChatInput() {
        $('#questionInput').prop('disabled', false);
        $('#askButton').prop('disabled', false);
    }
    
    function disableChatInput() {
        $('#questionInput').prop('disabled', true);
        $('#askButton').prop('disabled', true);
    }
});
