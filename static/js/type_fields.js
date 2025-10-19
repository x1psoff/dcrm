document.addEventListener('DOMContentLoaded', function() {
    const categorySelect = document.getElementById('id_category');

    if (categorySelect) {
        // Находим строки с полями по классам Django admin
        const hingeTypeRow = document.querySelector('.field-hinge_type');
        const answerTypeRow = document.querySelector('.field-answer_type');
        const runnerTypeRow = document.querySelector('.field-runner_type');

        if (hingeTypeRow && answerTypeRow && runnerTypeRow) {

            // Находим родительские элементы строк
            const hingeSection = hingeTypeRow.closest('.form-row').parentElement;
            const answerSection = answerTypeRow.closest('.form-row').parentElement;
            const runnerSection = runnerTypeRow.closest('.form-row').parentElement;

            function updateSectionsVisibility() {
                const selectedCategoryId = categorySelect.value;

                if (!selectedCategoryId) {
                    hideAllSections();
                    return;
                }

                // Получаем название выбранной категории
                const selectedOption = categorySelect.options[categorySelect.selectedIndex];
                const categoryName = selectedOption.text.toLowerCase();

                // Если категория содержит "петл" - показываем секции петель
                if (categoryName.includes('петл')) {
                    showSection(hingeSection);
                    showSection(answerSection);
                    hideSection(runnerSection);
                }
                // Если категория содержит "направля" - показываем секцию направляющих
                else if (categoryName.includes('направля')) {
                    hideSection(hingeSection);
                    hideSection(answerSection);
                    showSection(runnerSection);
                }
                // Для остальных категорий - скрываем все секции
                else {
                    hideAllSections();
                }
            }

            function showSection(section) {
                if (section) {
                    section.style.display = '';
                    // Также включаем поля внутри секции
                    const fields = section.querySelectorAll('select, input');
                    fields.forEach(field => field.disabled = false);
                }
            }

            function hideSection(section) {
                if (section) {
                    section.style.display = 'none';
                    // Также очищаем и отключаем поля внутри секции
                    const fields = section.querySelectorAll('select, input');
                    fields.forEach(field => {
                        if (field.type !== 'hidden') {
                            field.value = '';
                        }
                        field.disabled = true;
                    });
                }
            }

            function hideAllSections() {
                hideSection(hingeSection);
                hideSection(answerSection);
                hideSection(runnerSection);
            }

            // Сначала скрываем все секции
            hideAllSections();

            // Обновляем при загрузке и изменении
            updateSectionsVisibility();
            categorySelect.addEventListener('change', updateSectionsVisibility);
        }
    }
});