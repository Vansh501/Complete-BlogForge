document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 1. AJAX Comment Posting
    // -------------------------------------------------------------
    const commentForm = document.getElementById('comment-form');
    const commentsList = document.getElementById('comments-list');
    const noCommentsAlert = document.getElementById('no-comments-alert');

    if (commentForm) {
        commentForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = commentForm.querySelector('button[type="submit"]');
            const textarea = commentForm.querySelector('textarea[name="content"]');
            const content = textarea.value.trim();

            if (!content) return;

            // Set loading state
            const originalBtnText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Posting...';

            try {
                const csrfTokenInput = commentForm.querySelector('input[name="csrf_token"]');
                const csrfToken = csrfTokenInput ? csrfTokenInput.value : '';

                const response = await fetch(commentForm.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: new URLSearchParams({ content: content, csrf_token: csrfToken })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    // Create comment HTML element
                    const commentHtml = `
                        <div class="comment-card fade-in">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <div class="d-flex align-items-center">
                                    <img src="${data.comment.avatar_url}" alt="${data.comment.author}" class="user-avatar me-2" style="width: 32px; height: 32px;">
                                    <div>
                                        <span class="fw-bold text-white small">${data.comment.author}</span>
                                        <div class="text-muted" style="font-size: 0.75rem;">${data.comment.created_at}</div>
                                    </div>
                                </div>
                            </div>
                            <p class="mb-0 text-secondary" style="font-size: 0.95rem; white-space: pre-wrap;">${data.comment.content}</p>
                        </div>
                    `;

                    if (noCommentsAlert) {
                        noCommentsAlert.remove();
                    }

                    // Prepend or append the comment
                    commentsList.insertAdjacentHTML('afterbegin', commentHtml);
                    textarea.value = '';

                    // Scroll comment into view
                    commentsList.firstElementChild.scrollIntoView({ behavior: 'smooth' });
                } else {
                    alert(data.error || 'Failed to submit comment. Please try again.');
                }
            } catch (err) {
                console.error('Error posting comment:', err);
                alert('An error occurred. Check your network connection.');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        });
    }

    // -------------------------------------------------------------
    // 2. AI Co-pilot Integration inside Editor
    // -------------------------------------------------------------
    const aiOutlineBtn = document.getElementById('ai-outline-btn');
    const aiSummaryBtn = document.getElementById('ai-summary-btn');
    const aiTagsBtn = document.getElementById('ai-tags-btn');

    const titleInput = document.getElementById('title');
    const contentInput = document.getElementById('content');
    const summaryInput = document.getElementById('summary');
    const tagsInput = document.getElementById('tags');
    const aiStatusAlert = document.getElementById('ai-status-alert');

    // Helper to request data from local AI assist route
    async function requestAIAssist(action, bodyData) {
        const csrfTokenInput = document.querySelector('input[name="csrf_token"]');
        const csrfToken = csrfTokenInput ? csrfTokenInput.value : '';

        const response = await fetch('/ai/assist', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ action, ...bodyData })
        });
        return response.json();
    }

    // Show alert helper
    function showAIStatus(message, isWarning = false) {
        if (!aiStatusAlert) return;
        aiStatusAlert.className = `alert alert-${isWarning ? 'warning' : 'info'} alert-dismissible fade show d-flex align-items-center mb-3`;
        aiStatusAlert.innerHTML = `
            <i class="bi bi-info-circle-fill me-2 fs-5"></i>
            <div>${message}</div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        aiStatusAlert.classList.remove('d-none');

        if (window.aiAlertTimeout) {
            clearTimeout(window.aiAlertTimeout);
        }
        window.aiAlertTimeout = setTimeout(() => {
            aiStatusAlert.classList.remove('show');
            setTimeout(() => {
                aiStatusAlert.classList.add('d-none');
            }, 150);
        }, 5000);
    }

    // AI Outline generator
    if (aiOutlineBtn) {
        aiOutlineBtn.addEventListener('click', async () => {
            const title = titleInput.value.trim();
            if (!title) {
                alert('Please enter a post title first to generate an outline.');
                return;
            }

            const originalBtnText = aiOutlineBtn.innerHTML;
            aiOutlineBtn.disabled = true;
            aiOutlineBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Generating...';

            try {
                const data = await requestAIAssist('outline', { title });
                if (data.status === 'success') {
                    // Prepend or insert outline into Content textarea
                    const prefix = data.result + "\n\n---\n\n";
                    contentInput.value = prefix + contentInput.value;
                    showAIStatus('AI Outline generated and inserted at the beginning of your content!');
                } else if (data.status === 'offline') {
                    showAIStatus(data.message, true);
                    // Insert mock outline
                    const prefix = data.mock_data + "\n\n---\n\n";
                    contentInput.value = prefix + contentInput.value;
                } else {
                    alert(data.message || data.error || 'Failed to generate outline.');
                }
            } catch (err) {
                console.error(err);
                alert('Error contacting server.');
            } finally {
                aiOutlineBtn.disabled = false;
                aiOutlineBtn.innerHTML = originalBtnText;
            }
        });
    }

    // AI Summary generator
    if (aiSummaryBtn) {
        aiSummaryBtn.addEventListener('click', async () => {
            const content = contentInput.value.trim();
            if (!content) {
                alert('Please write some content first so the AI can summarize it.');
                return;
            }

            const originalBtnText = aiSummaryBtn.innerHTML;
            aiSummaryBtn.disabled = true;
            aiSummaryBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Summarizing...';

            try {
                const data = await requestAIAssist('summary', { content });
                if (data.status === 'success') {
                    summaryInput.value = data.result;
                    showAIStatus('AI Post Summary generated!');
                } else if (data.status === 'offline') {
                    showAIStatus(data.message, true);
                    summaryInput.value = data.mock_data;
                } else {
                    alert(data.message || data.error || 'Failed to generate summary.');
                }
            } catch (err) {
                console.error(err);
                alert('Error contacting server.');
            } finally {
                aiSummaryBtn.disabled = false;
                aiSummaryBtn.innerHTML = originalBtnText;
            }
        });
    }

    // AI Tags suggester
    if (aiTagsBtn) {
        aiTagsBtn.addEventListener('click', async () => {
            const content = contentInput.value.trim();
            if (!content) {
                alert('Please write some content first so the AI can suggest tags.');
                return;
            }

            const originalBtnText = aiTagsBtn.innerHTML;
            aiTagsBtn.disabled = true;
            aiTagsBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Analyzing...';

            try {
                const data = await requestAIAssist('tags', { content });
                if (data.status === 'success') {
                    tagsInput.value = data.result;
                    showAIStatus('AI suggested tags updated!');
                } else if (data.status === 'offline') {
                    showAIStatus(data.message, true);
                    tagsInput.value = data.mock_data;
                } else {
                    alert(data.message || data.error || 'Failed to suggest tags.');
                }
            } catch (err) {
                console.error(err);
                alert('Error contacting server.');
            } finally {
                aiTagsBtn.disabled = false;
                aiTagsBtn.innerHTML = originalBtnText;
            }
        });
    }

    // -------------------------------------------------------------
    // 3. Top Progress Loading Bar
    // -------------------------------------------------------------
    const forms = document.querySelectorAll('form');
    const loadingBar = document.getElementById('top-loading-bar');
    forms.forEach(form => {
        form.addEventListener('submit', () => {
            if (loadingBar) {
                loadingBar.style.width = '70%';
                setTimeout(() => {
                    loadingBar.style.width = '90%';
                }, 400);
            }
        });
    });

    // -------------------------------------------------------------
    // 4. Auto-dismiss Flash Alerts
    // -------------------------------------------------------------
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        if (alert.id === 'ai-status-alert') return;
        
        setTimeout(() => {
            if (typeof bootstrap !== 'undefined') {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
                if (bsAlert) {
                    bsAlert.close();
                    return;
                }
            }
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, 5000);
    });
});
