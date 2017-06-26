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
                termConcludeDate: '=',
                isSelectedDateInPast: '='
            },
            templateUrl: 'partials/hu-date-picker.html',
            link: function (scope, element) {
                $('#dp-alert').hide();
                // Create the date picker on the input tag.
                var inputElement = $(element).find('input');
                var dp = inputElement.datepicker('setDate', scope.modelValue);
                dp.on('changeDate', function() {
                    var selectedDate = inputElement.val();
                    // If the selected date is in the past then display alert message and reset the date.
                    if (scope.isSelectedDateInPast(selectedDate)) {
                        $('#dp-alert').show();
                    } else {
                        // If the selected date is a current or future date, make sure the alert is hidden.
                        $('#dp-alert').hide();
                    }
                });
            }
        };
    }
})();
