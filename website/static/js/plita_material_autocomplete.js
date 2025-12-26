// Автодополнение для поля материала плиты в админке
(function($) {
    $(document).ready(function() {
        const materialField = $('#id_material');
        
        if (materialField.length) {
            // Получаем список материалов из data-атрибута
            const materialsStr = materialField.attr('data-materials');
            const materials = materialsStr ? materialsStr.split(',') : [];
            
            // Создаем datalist для автодополнения
            const datalistId = 'material-datalist';
            let datalist = $('#' + datalistId);
            
            if (datalist.length === 0) {
                datalist = $('<datalist>').attr('id', datalistId);
                materialField.after(datalist);
                materialField.attr('list', datalistId);
            }
            
            // Добавляем опции в datalist
            materials.forEach(function(material) {
                if (material && material.trim()) {
                    const option = $('<option>').attr('value', material.trim());
                    datalist.append(option);
                }
            });
            
            // Добавляем популярные материалы, если их нет
            const popularMaterials = ['ЛДСП', 'МДФ', 'Пленка', 'Другой'];
            popularMaterials.forEach(function(material) {
                if (materials.indexOf(material) === -1) {
                    const option = $('<option>').attr('value', material);
                    datalist.append(option);
                }
            });
        }
    });
})(django.jQuery);

