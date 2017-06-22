(function() {
    var app = angular.module('CourseInfo');
    app.directive('huDatePicker', huDatePicker);

    function huDatePicker() {
        return {
            restrict: 'E',
            scope: {
                editable: '<',  // if not provided, defaults to null/false
                field: '@',
                formValue: '=',
                isLoading: '&',
                label: '@',
                modelValue: '=',
                term: '=',
                termConcludeDate: '='
            },
            templateUrl: 'partials/hu-date-picker.html',
            link: function (scope, element) {
                $('#dp-alert').hide();
                // Create the date picker on the input tag.
                var inputElement = $(element).find('input');
                var dp = inputElement.datepicker('setDate', scope.modelValue);
                dp.change(function() {
                    var selectedDate = inputElement.val();
                    // If the selected date is in the past then display alert message and reset the date.
                    if (isSelectedDateInPast(selectedDate)) {
                        inputElement.val(scope.modelValue);
                        inputElement.datepicker('setDate', scope.modelValue);
                        $('#dp-alert').show();
                    }
                });
            }
        };
    }

    // Checks if the given date is prior to today's date.
    function isSelectedDateInPast(selectedDate) {
        // Since the input field is a string representation of a date,
        // we need to convert today's date to the same format as a string to make the comparison.
        var today = new Date();
        today = (today.getMonth() + 1) + '/' + today.getDate() + '/' +  today.getFullYear();
        return Date.parse(selectedDate)-Date.parse(today)<0
    }
})();
