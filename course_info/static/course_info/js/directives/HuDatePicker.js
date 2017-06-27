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
                isSelectedDateInPast: '=',
                toggleDatePickerAlert: '='
            },
            templateUrl: 'partials/hu-date-picker.html',
            link: function (scope, element) {
                // Create the date picker on the input tag.
                var inputElement = $(element).find('input');
                var dp = inputElement.datepicker('setDate', scope.modelValue);
                dp.on('changeDate', function() {
                    var selectedDate = inputElement.val();
                    // If the selected date is in the past then display alert message and reset the date.
                    if (scope.isSelectedDateInPast(selectedDate)) {
                        scope.toggleDatePickerAlert(true);
                    } else {
                        // If the selected date is a current or future date, make sure the alert is hidden.
                        scope.toggleDatePickerAlert(false);
                    }
                });
            }
        };
    }
})();
