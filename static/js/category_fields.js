// Автоматическое обновление полей при изменении категории
(function($) {
    $(document).ready(function() {
        var categoryField = $('#id_category');
        
        if (categoryField.length) {
            // При изменении категории перезагружаем страницу
            categoryField.on('change', function() {
                var categoryId = $(this).val();
                if (categoryId) {
                    // Сохраняем текущие значения полей
                    var formData = {};
                    $('input, select, textarea').each(function() {
                        var name = $(this).attr('name');
                        if (name && name.startsWith('custom_field_')) {
                            formData[name] = $(this).val();
                        }
                    });
                    
                    // Перезагружаем страницу с новой категорией
                    var url = window.location.href;
                    if (url.indexOf('?') > -1) {
                        url = url.split('?')[0];
                    }
                    // Добавляем параметр категории для сохранения выбора
                    window.location.href = url + '?category=' + categoryId;
                }
            });
        }
    });
})(django.jQuery);

