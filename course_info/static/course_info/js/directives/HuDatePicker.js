(function() {
    var app = angular.module('CourseInfo');
    app.directive('huDatePicker', huDatePicker);

    function huDatePicker(){
        return {
            restrict: 'E',
            scope: {
                editable: '<',  // if not provided, defaults to null/false
                field: '@',
                formValue: '=',
                isLoading: '&',
                label: '@',
                maxlength: '@',
                modelValue: '='
            },
            templateUrl: 'partials/hu-date-picker.html',
        };
    }

})();
