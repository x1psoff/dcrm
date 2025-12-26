// JavaScript для улучшения работы с фильтрами продуктов
document.addEventListener('DOMContentLoaded', function() {
    const filterForm = document.getElementById('filterForm');
    
    if (!filterForm) return;
    
    // Автоматическая отправка формы при изменении фильтров (опционально)
    const autoSubmit = false; // Измените на true для автоматической фильтрации
    
    if (autoSubmit) {
        const filterInputs = filterForm.querySelectorAll('select, input[type="radio"]');
        
        filterInputs.forEach(function(input) {
            input.addEventListener('change', function() {
                // Небольшая задержка для лучшего UX
                setTimeout(function() {
                    filterForm.submit();
                }, 300);
            });
        });
    }
    
    // Показываем/скрываем фильтры категорий при выборе категории
    const categorySelect = document.querySelector('select[name="category"]');
    
    if (categorySelect) {
        // Функция для показа/скрытия фильтров по категории
        function toggleCategoryFilters() {
            const selectedCategory = categorySelect.options[categorySelect.selectedIndex]?.text || '';
            
            // Получаем все динамические фильтры
            const dynamicFilters = filterForm.querySelectorAll('select[data-category]');
            
            dynamicFilters.forEach(function(filter) {
                const filterCategory = filter.getAttribute('data-category');
                const filterWrapper = filter.closest('.mb-2') || filter.closest('div');
                
                if (filterWrapper) {
                    // Показываем только фильтры выбранной категории
                    if (!selectedCategory || selectedCategory === 'Все категории' || filterCategory === selectedCategory) {
                        filterWrapper.style.display = 'block';
                    } else {
                        filterWrapper.style.display = 'none';
                        // Сбрасываем значение скрытого фильтра
                        filter.value = '';
                    }
                }
            });
        }
        
        // Применяем при загрузке страницы
        toggleCategoryFilters();
        
        // Применяем при изменении категории
        categorySelect.addEventListener('change', toggleCategoryFilters);
    }
    
    // Индикатор активных фильтров
    function updateFilterCount() {
        const activeFilters = [];
        
        // Проверяем все поля формы
        const formData = new FormData(filterForm);
        
        for (let [key, value] of formData.entries()) {
            if (value && value !== '' && key !== 'csrfmiddlewaretoken') {
                activeFilters.push(key);
            }
        }
        
        // Показываем количество активных фильтров (опционально)
        const filterButton = filterForm.querySelector('button[type="submit"]');
        if (filterButton && activeFilters.length > 0) {
            const badge = filterButton.querySelector('.badge') || document.createElement('span');
            badge.className = 'badge bg-danger ms-2';
            badge.textContent = activeFilters.length;
            
            if (!filterButton.querySelector('.badge')) {
                filterButton.appendChild(badge);
            }
        }
    }
    
    updateFilterCount();
    
    // Сворачивание/разворачивание секций фильтров
    const advancedFiltersToggle = document.querySelector('[data-bs-toggle="collapse"]');
    
    if (advancedFiltersToggle) {
        const icon = advancedFiltersToggle.querySelector('i');
        const target = document.querySelector(advancedFiltersToggle.getAttribute('data-bs-target'));
        
        if (target && icon) {
            target.addEventListener('shown.bs.collapse', function() {
                icon.classList.remove('bi-chevron-down');
                icon.classList.add('bi-chevron-up');
            });
            
            target.addEventListener('hidden.bs.collapse', function() {
                icon.classList.remove('bi-chevron-up');
                icon.classList.add('bi-chevron-down');
            });
        }
    }
    
    // Улучшенная подсветка выбранных элементов
    const checkboxes = document.querySelectorAll('.form-check-input[type="checkbox"]');
    
    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            const listItem = this.closest('.list-group-item');
            
            if (listItem) {
                if (this.checked) {
                    listItem.style.backgroundColor = '#f0f8ff';
                    listItem.style.borderLeft = '3px solid #0d6efd';
                } else {
                    listItem.style.backgroundColor = '';
                    listItem.style.borderLeft = '';
                }
            }
        });
        
        // Применяем стили при загрузке страницы
        if (checkbox.checked) {
            const listItem = checkbox.closest('.list-group-item');
            if (listItem) {
                listItem.style.backgroundColor = '#f0f8ff';
                listItem.style.borderLeft = '3px solid #0d6efd';
            }
        }
    });
    
    // Сохранение позиции прокрутки
    const scrollPosition = sessionStorage.getItem('scrollPosition');
    if (scrollPosition) {
        window.scrollTo(0, parseInt(scrollPosition));
        sessionStorage.removeItem('scrollPosition');
    }
    
    filterForm.addEventListener('submit', function() {
        sessionStorage.setItem('scrollPosition', window.scrollY);
    });
    
    // Быстрая очистка всех фильтров
    const resetButton = filterForm.querySelector('a[href*="add_products_to_record"]');
    
    if (resetButton) {
        resetButton.addEventListener('click', function(e) {
            // Очищаем все поля формы
            filterForm.reset();
            
            // Очищаем сохраненные данные
            sessionStorage.removeItem('scrollPosition');
        });
    }
    
    // Подсказки для пустых результатов
    const itemsList = document.querySelector('.list-group');
    
    if (itemsList) {
        const items = itemsList.querySelectorAll('.list-group-item:not(.border-0.text-center)');
        
        if (items.length === 0) {
            // Добавляем полезную подсказку
            const emptyMessage = itemsList.querySelector('.text-center.py-5 p');
            
            if (emptyMessage) {
                emptyMessage.innerHTML = `
                    Комплектующие не найдены.<br>
                    <small class="text-muted">Попробуйте изменить фильтры или <a href="${window.location.pathname}" class="text-primary">сбросить все фильтры</a></small>
                `;
            }
        }
    }
});

