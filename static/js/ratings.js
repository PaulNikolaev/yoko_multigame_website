document.addEventListener('DOMContentLoaded', function() {
    // Получаем CSRF-токен из мета-тега (добавленного в main.html)
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').content;
    // Получаем статус аутентификации пользователя из data-атрибута body
    const isAuthenticated = document.body.dataset.userAuthenticated === 'true';

    // Находим все контейнеры с кнопками рейтинга
    const ratingButtonsContainers = document.querySelectorAll('.rating-buttons');

    ratingButtonsContainers.forEach(container => {
        const postId = container.dataset.postId; // ID поста
        const likeButton = container.querySelector('.like-button');
        const dislikeButton = container.querySelector('.dislike-button');
        const ratingSumElement = container.querySelector('.rating-sum');

        // --- Инициализация состояния кнопок при загрузке страницы ---
        function initializeButtonsState() {
            if (!isAuthenticated) {
                // Если пользователь не аутентифицирован, отключаем кнопки
                if (likeButton) likeButton.disabled = true;
                if (dislikeButton) dislikeButton.disabled = true;
                // Можно добавить всплывающее сообщение для пользователя
                // или изменить внешний вид кнопок на более "неактивный"
                return; // Выходим, так как кнопки отключены
            }

            // Если пользователь аутентифицирован, проверяем его текущий голос
            if (likeButton) {
                const currentVote = parseInt(likeButton.dataset.currentVote);
                if (currentVote === 1) {
                    likeButton.classList.add('active'); // Или 'btn-success'
                    likeButton.classList.remove('btn-outline-success');
                } else {
                    likeButton.classList.remove('active', 'btn-success');
                    likeButton.classList.add('btn-outline-success');
                }
            }
            if (dislikeButton) {
                const currentVote = parseInt(dislikeButton.dataset.currentVote);
                if (currentVote === -1) {
                    dislikeButton.classList.add('active'); // Или 'btn-danger'
                    dislikeButton.classList.remove('btn-outline-danger');
                } else {
                    dislikeButton.classList.remove('active', 'btn-danger');
                    dislikeButton.classList.add('btn-outline-danger');
                }
            }
        }

        // Вызываем инициализацию при загрузке
        initializeButtonsState();

        // --- Обработчик клика по кнопкам рейтинга ---
        function handleRatingClick(event) {
            // Если пользователь не аутентифицирован, выходим (кнопки уже должны быть disabled, но это дополнительная защита)
            if (!isAuthenticated) {
                alert('Пожалуйста, войдите в систему, чтобы оценить эту запись.');
                return;
            }

            const value = parseInt(event.currentTarget.dataset.value); // 1 или -1

            const formData = new FormData();
            formData.append('post_id', postId);
            formData.append('value', value);

            fetch("/rating/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken,
                    "X-Requested-With": "XMLHttpRequest", // Django может использовать это для проверки AJAX
                },
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    // Обработка ошибок, например, 403 (Forbidden)
                    return response.json().then(err => {
                        throw new Error(err.error || 'Произошла ошибка при отправке оценки.');
                    });
                }
                return response.json();
            })
            .then(data => {
                if (ratingSumElement) {
                    ratingSumElement.textContent = data.rating_sum;
                }
                // Обновляем состояние кнопок после успешной отправки
                // Это может быть сделано через перезапрос currentVote или просто изменением классов
                // Для простоты, мы можем изменить класс кнопки, чтобы показать ее активность/неактивность

                // Если лайк был нажат
                if (value === 1) {
                    if (likeButton.classList.contains('active')) {
                        // Если уже активен, значит отменяем лайк
                        likeButton.classList.remove('active', 'btn-success');
                        likeButton.classList.add('btn-outline-success');
                    } else {
                        // Лайкаем
                        likeButton.classList.add('active', 'btn-success');
                        likeButton.classList.remove('btn-outline-success');
                        // Если дизлайк был активен, отменяем его
                        dislikeButton.classList.remove('active', 'btn-danger');
                        dislikeButton.classList.add('btn-outline-danger');
                    }
                }
                // Если дизлайк был нажат
                else if (value === -1) {
                    if (dislikeButton.classList.contains('active')) {
                        // Если уже активен, значит отменяем дизлайк
                        dislikeButton.classList.remove('active', 'btn-danger');
                        dislikeButton.classList.add('btn-outline-danger');
                    } else {
                        // Дизлайкаем
                        dislikeButton.classList.add('active', 'btn-danger');
                        dislikeButton.classList.remove('btn-outline-danger');
                        // Если лайк был активен, отменяем его
                        likeButton.classList.remove('active', 'btn-success');
                        likeButton.classList.add('btn-outline-success');
                    }
                }
            })
            .catch(error => {
                console.error("Ошибка при отправке рейтинга:", error);
                alert(error.message || 'Не удалось обновить рейтинг. Пожалуйста, попробуйте позже.');
            });
        }

        // Прикрепляем обработчики событий
        if (likeButton) likeButton.addEventListener('click', handleRatingClick);
        if (dislikeButton) dislikeButton.addEventListener('click', handleRatingClick);
    });
});