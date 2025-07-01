document.addEventListener('DOMContentLoaded', function() {
    // Инициализация Flatpickr
    flatpickr("#id_birth_date", {
        dateFormat: "d.m.Y",
        locale: "ru",
        allowInput: true,
    });

    // Select2 для страны
    var $countrySelect = $('#id_country').select2({
        placeholder: "Выберите страну",
        allowClear: true,
        language: "ru"
    });

    // Select2 для города
    var $citySelect = $('#id_city');

    $citySelect.select2({
        placeholder: "Введите город",
        allowClear: true,
        language: "ru",
        ajax: {
            url: $citySelect.data('city-autocomplete-url'),
            dataType: 'json',
            delay: 250,
            data: function (params) {
                let countryCode = $countrySelect.val();
                return {
                    term: params.term,
                    country_id: countryCode
                };
            },
            processResults: function (data) {
                return {
                    results: data.results
                };
            },
            cache: true
        },
        minimumInputLength: 2,
        templateSelection: function (data) {
            return data.text || data.id;
        }
    });

    var $initialCityValueElement = $('#city_initial_value');
    if ($initialCityValueElement.length && $initialCityValueElement.data('initial-city')) {
        var initialCityNameFromDjango = $initialCityValueElement.data('initial-city');
        console.log("Найдено начальное значение города из Django:", initialCityNameFromDjango);

        var initialOption = new Option(initialCityNameFromDjango, initialCityNameFromDjango, true, true);

        $citySelect.append(initialOption).trigger('change');

        console.log("Город должен был быть установлен в Select2.");
    } else {
        console.log("Нет начального значения города для установки.");
    }


    // Логика для очистки города при смене страны
    $countrySelect.on('change', function() {
        $citySelect.val(null).trigger('change');
    });
});