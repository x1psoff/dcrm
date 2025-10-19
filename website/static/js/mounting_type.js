document.addEventListener('DOMContentLoaded', function() {
    const categorySelect = document.getElementById('id_category');
    const mountingTypeSelect = document.getElementById('id_mounting_type');
    const responseTypeSelect = document.getElementById('id_response_type');
    const hingeAngleSelect = document.getElementById('id_hinge_angle');
    const hingeClosingTypeSelect = document.getElementById('id_hinge_closing_type');
    const runnerSizeSelect = document.getElementById('id_runner_size');

    if (categorySelect && mountingTypeSelect && responseTypeSelect && hingeAngleSelect && hingeClosingTypeSelect && runnerSizeSelect) {
        // Опции для mounting_type
        const mountingOptions = {
            'default': [
                {value: '', text: '--- Выберите тип ---'}
            ],
            'петл': [
                {value: '', text: '--- Выберите тип ---'},
                {value: 'Накладная', text: 'Накладная'},
                {value: 'Полунакладная', text: 'Полунакладная'},
                {value: 'Вкладная', text: 'Вкладная'},
                {value: 'Фальш-планка', text: 'Фальш-планка'}
            ],
            'направля': [
                {value: '', text: '--- Выберите тип ---'},
                {value: 'Шариковые', text: 'Шариковые'},
                {value: 'Роликовые', text: 'Роликовые'},
                {value: 'Метабокс', text: 'Метабокс'},
                {value: 'Cкрытого_монтажа', text: 'Cкрытого_монтажа'},
                {value: 'Частички', text: 'Частички'}
            ]
        };

        // Опции для response_type (ответка для петель)
        const responseOptions = [
            {value: '', text: '--- Выберите ответку ---'},
            {value: 'Прямая', text: 'Прямая'},
            {value: 'Крестообразная', text: 'Крестообразная'}
        ];

        // Опции для hinge_angle (угол открывания)
        const hingeAngleOptions = [
            {value: '', text: '--- Выберите угол ---'},
            {value: '83', text: '83°'},
            {value: '95', text: '95°'},
            {value: '110', text: '110°'},
            {value: '165', text: '165°'}
        ];

        // Опции для hinge_closing_type (тип закрывания)
        const hingeClosingOptions = [
            {value: '', text: '--- Выберите тип ---'},
            {value: 'с доводчиком', text: 'с доводчиком'},
            {value: 'без доводчика', text: 'без доводчика'},
            {value: 'без пружинки', text: 'без пружинки'}
        ];

        // Опции для runner_size (размеры для направляющих)
        const runnerSizeOptions = [
            {value: '', text: '--- Выберите размер ---'},
            {value: '250', text: '250 мм'},
            {value: '270', text: '270 мм'},
            {value: '300', text: '300 мм'},
            {value: '310', text: '310 мм'},
            {value: '350', text: '350 мм'},
            {value: '360', text: '360 мм'},
            {value: '400', text: '400 мм'},
            {value: '410', text: '410 мм'},
            {value: '450', text: '450 мм'},
            {value: '460', text: '460 мм'},
            {value: '500', text: '500 мм'},
            {value: '510', text: '510 мм'},
            {value: '550', text: '550 мм'},
            {value: '560', text: '560 мм'},
            {value: '600', text: '600 мм'},
            {value: '650', text: '650 мм'},
            {value: '700', text: '700 мм'},
            {value: '750', text: '750 мм'}
        ];

        // Находим родительские строки
        const mountingTypeRow = mountingTypeSelect.closest('.form-row');
        const responseTypeRow = responseTypeSelect.closest('.form-row');
        const hingeAngleRow = hingeAngleSelect.closest('.form-row');
        const hingeClosingRow = hingeClosingTypeSelect.closest('.form-row');
        const runnerSizeRow = runnerSizeSelect.closest('.form-row');

        // СОХРАНЯЕМ ТЕКУЩИЕ ЗНАЧЕНИЯ ПРОДУКТА
        const currentValues = {
            mounting_type: mountingTypeSelect.value,
            response_type: responseTypeSelect.value,
            hinge_angle: hingeAngleSelect.value,
            hinge_closing_type: hingeClosingTypeSelect.value,
            runner_size: runnerSizeSelect.value
        };

        function updateTypeOptions() {
            const selectedCategoryId = categorySelect.value;

            // ВСЕГДА показываем все поля, если у них есть значения
            if (currentValues.mounting_type) mountingTypeRow.style.display = '';
            if (currentValues.response_type) responseTypeRow.style.display = '';
            if (currentValues.hinge_angle) hingeAngleRow.style.display = '';
            if (currentValues.hinge_closing_type) hingeClosingRow.style.display = '';
            if (currentValues.runner_size) runnerSizeRow.style.display = '';

            if (!selectedCategoryId) {
                setMountingOptions(mountingOptions.default, currentValues.mounting_type);
                setResponseOptions(responseOptions, currentValues.response_type);
                setHingeAngleOptions(hingeAngleOptions, currentValues.hinge_angle);
                setHingeClosingOptions(hingeClosingOptions, currentValues.hinge_closing_type);
                setRunnerSizeOptions(runnerSizeOptions, currentValues.runner_size);

                // Скрываем поля только если у них нет значений
                if (!currentValues.response_type) responseTypeRow.style.display = 'none';
                if (!currentValues.hinge_angle) hingeAngleRow.style.display = 'none';
                if (!currentValues.hinge_closing_type) hingeClosingRow.style.display = 'none';
                if (!currentValues.runner_size) runnerSizeRow.style.display = 'none';
                return;
            }

            // Получаем название выбранной категории
            const selectedOption = categorySelect.options[categorySelect.selectedIndex];
            const categoryName = selectedOption.text.toLowerCase();

            // Определяем какие опции показывать
            let mountingOptionsToUse;
            if (categoryName.includes('петл')) {
                mountingOptionsToUse = mountingOptions['петл'];
                // Показываем поля для петель, если у них есть значения
                if (!currentValues.response_type) {
                    setResponseOptions(responseOptions, currentValues.response_type);
                    responseTypeRow.style.display = '';
                }
                if (!currentValues.hinge_angle) {
                    setHingeAngleOptions(hingeAngleOptions, currentValues.hinge_angle);
                    hingeAngleRow.style.display = '';
                }
                if (!currentValues.hinge_closing_type) {
                    setHingeClosingOptions(hingeClosingOptions, currentValues.hinge_closing_type);
                    hingeClosingRow.style.display = '';
                }
                // Скрываем runner_size, если у него нет значения
                if (!currentValues.runner_size) runnerSizeRow.style.display = 'none';
            } else if (categoryName.includes('направля')) {
                mountingOptionsToUse = mountingOptions['направля'];
                // Скрываем поля для петель, если у них нет значений
                if (!currentValues.response_type) responseTypeRow.style.display = 'none';
                if (!currentValues.hinge_angle) hingeAngleRow.style.display = 'none';
                if (!currentValues.hinge_closing_type) hingeClosingRow.style.display = 'none';
                // Показываем runner_size, если у него есть значение
                if (!currentValues.runner_size) {
                    setRunnerSizeOptions(runnerSizeOptions, currentValues.runner_size);
                    runnerSizeRow.style.display = '';
                }
            } else {
                mountingOptionsToUse = mountingOptions.default;
                // Скрываем поля только если у них нет значений
                if (!currentValues.response_type) responseTypeRow.style.display = 'none';
                if (!currentValues.hinge_angle) hingeAngleRow.style.display = 'none';
                if (!currentValues.hinge_closing_type) hingeClosingRow.style.display = 'none';
                if (!currentValues.runner_size) runnerSizeRow.style.display = 'none';
            }

            setMountingOptions(mountingOptionsToUse, currentValues.mounting_type);
        }

        function setMountingOptions(options, currentValue) {
            // Очищаем и заполняем select
            mountingTypeSelect.innerHTML = '';
            options.forEach(option => {
                const optElement = document.createElement('option');
                optElement.value = option.value;
                optElement.textContent = option.text;
                mountingTypeSelect.appendChild(optElement);
            });

            // Устанавливаем значение ПОСЛЕ заполнения options
            if (currentValue && options.some(opt => opt.value === currentValue)) {
                mountingTypeSelect.value = currentValue;
            }
        }

        function setResponseOptions(options, currentValue) {
            // Очищаем и заполняем select
            responseTypeSelect.innerHTML = '';
            options.forEach(option => {
                const optElement = document.createElement('option');
                optElement.value = option.value;
                optElement.textContent = option.text;
                responseTypeSelect.appendChild(optElement);
            });

            // Устанавливаем значение ПОСЛЕ заполнения options
            if (currentValue && options.some(opt => opt.value === currentValue)) {
                responseTypeSelect.value = currentValue;
            }
        }

        function setHingeAngleOptions(options, currentValue) {
            // Очищаем и заполняем select
            hingeAngleSelect.innerHTML = '';
            options.forEach(option => {
                const optElement = document.createElement('option');
                optElement.value = option.value;
                optElement.textContent = option.text;
                hingeAngleSelect.appendChild(optElement);
            });

            // Устанавливаем значение ПОСЛЕ заполнения options
            if (currentValue && options.some(opt => opt.value === currentValue)) {
                hingeAngleSelect.value = currentValue;
            }
        }

        function setHingeClosingOptions(options, currentValue) {
            // Очищаем и заполняем select
            hingeClosingTypeSelect.innerHTML = '';
            options.forEach(option => {
                const optElement = document.createElement('option');
                optElement.value = option.value;
                optElement.textContent = option.text;
                hingeClosingTypeSelect.appendChild(optElement);
            });

            // Устанавливаем значение ПОСЛЕ заполнения options
            if (currentValue && options.some(opt => opt.value === currentValue)) {
                hingeClosingTypeSelect.value = currentValue;
            }
        }

        function setRunnerSizeOptions(options, currentValue) {
            // Очищаем и заполняем select
            runnerSizeSelect.innerHTML = '';
            options.forEach(option => {
                const optElement = document.createElement('option');
                optElement.value = option.value;
                optElement.textContent = option.text;
                runnerSizeSelect.appendChild(optElement);
            });

            // Устанавливаем значение ПОСЛЕ заполнения options
            if (currentValue && options.some(opt => opt.value === currentValue)) {
                runnerSizeSelect.value = currentValue;
            }
        }

        // Инициализируем при загрузке
        updateTypeOptions();
        categorySelect.addEventListener('change', updateTypeOptions);
    }
});