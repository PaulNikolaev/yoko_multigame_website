document.addEventListener('DOMContentLoaded', function () {
    const commentForm = document.forms.commentForm;
    const commentFormContent = commentForm.content;
    const commentFormParentInput = commentForm.parent;
    const commentFormSubmit = commentForm.commentSubmit;
    const commentPostId = commentForm.getAttribute('data-post-id');

    const replyToInfo = document.getElementById('reply-to-info');
    const replyUsernameSpan = document.getElementById('reply-username');
    const cancelReplyBtn = document.getElementById('cancel-reply-btn');

    // --- Функции-обработчики событий ---

    // Функция для инициализации всех слушателей событий на комментариях
    function initializeCommentEventListeners() {
        // Инициализация кнопок "Ответить"
        document.querySelectorAll('.btn-reply').forEach(button => {
            button.removeEventListener('click', replyComment);
            button.addEventListener('click', replyComment);
        });

        // Инициализация кнопок сворачивания/разворачивания
        document.querySelectorAll('.toggle-replies-btn').forEach(button => {
            button.removeEventListener('click', toggleReplies);
            button.addEventListener('click', toggleReplies);
        });
    }

    // Обработчик для кнопки "Ответить"
    function replyComment(e) {
        e.preventDefault();
        const commentUsername = this.dataset.commentUsername;
        const commentId = this.dataset.commentId;

        commentFormContent.value = `${commentUsername}, `;
        commentFormContent.focus();
        commentFormParentInput.value = commentId;

        replyUsernameSpan.textContent = commentUsername;
        replyToInfo.classList.remove('d-none');
        commentForm.scrollIntoView({behavior: 'smooth'});
    }

    // Обработчик для кнопки отмены ответа
    function cancelReply() {
        commentFormParentInput.value = '';
        replyToInfo.classList.add('d-none');
        replyUsernameSpan.textContent = '';
    }

    // Обработчик для кнопки сворачивания/разворачивания ответов
    function toggleReplies() {
        const targetId = this.dataset.bsTarget;
        const repliesContainer = document.querySelector(targetId);

        if (repliesContainer) {
            if (repliesContainer.classList.contains('show')) {
                this.innerHTML = `Показать ответы (<span class="replies-count">${this.querySelector('.replies-count').textContent}</span>)`;
            } else {
                this.innerHTML = `Свернуть ответы (<span class="replies-count">${this.querySelector('.replies-count').textContent}</span>)`;
            }
        }
    }

    // --- Основная функция отправки комментария ---
    commentForm.addEventListener('submit', async function (event) {
        event.preventDefault();

        commentFormSubmit.disabled = true;
        commentFormSubmit.innerText = "Отправка...";

        try {
            const formData = new FormData(commentForm);

            const response = await fetch(`/post/${commentPostId}/comments/create/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrftoken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData,
            });

            // Проверяем статус ответа
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Server error: ${response.status}`);
            }

            const data = await response.json();

            if (data.success) {
                const parentId = commentFormParentInput.value;
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = data.comment_html.trim();

                const newCommentNode = tempDiv.firstChild;

                if (parentId) {
                    const parentRepliesContainer = document.querySelector(`#replies-${parentId}`);
                    if (parentRepliesContainer) {
                        parentRepliesContainer.appendChild(newCommentNode);

                        if (!parentRepliesContainer.classList.contains('show')) {
                            const parentToggleButton = parentRepliesContainer.parentNode.querySelector('.toggle-replies-btn');
                            if (parentToggleButton) {
                                const bsCollapse = new bootstrap.Collapse(parentRepliesContainer, {toggle: false});
                                bsCollapse.show();
                                parentToggleButton.innerHTML = `Свернуть ответы (<span class="replies-count">${parentToggleButton.querySelector('.replies-count').textContent}</span>)`;
                            }
                        }

                        // Обновляем счетчик ответов на родительской кнопке
                        const parentToggleButtonCountSpan = parentRepliesContainer.parentNode.querySelector('.toggle-replies-btn .replies-count');
                        if (parentToggleButtonCountSpan) {
                            parentToggleButtonCountSpan.textContent = parseInt(parentToggleButtonCountSpan.textContent) + 1;
                            const parentToggleButton = parentRepliesContainer.parentNode.querySelector('.toggle-replies-btn');
                            if (parentToggleButton) {
                                parentToggleButton.innerHTML = `Свернуть ответы (<span class="replies-count">${parentToggleButtonCountSpan.textContent}</span>)`;
                            }
                        }

                    } else {
                        document.querySelector('.nested-comments').appendChild(newCommentNode);
                        console.warn(`Parent replies container with ID #replies-${parentId} not found. Appending as root comment.`);
                    }
                } else {
                    document.querySelector('.nested-comments').appendChild(newCommentNode);
                }

                commentForm.reset();
                cancelReply();
                initializeCommentEventListeners();

            } else {
                console.error('Ошибка при добавлении комментария (success: false):', data.errors || data.error);
            }
        } catch (error) {
            console.error('Произошла ошибка AJAX или сервера:', error);
        } finally {
            commentFormSubmit.disabled = false;
            commentFormSubmit.innerText = "Добавить комментарий";
        }
    });

    // Инициализируем слушатели при первой загрузке страницы
    initializeCommentEventListeners();
    if (cancelReplyBtn) {
        cancelReplyBtn.addEventListener('click', cancelReply);
    }
});