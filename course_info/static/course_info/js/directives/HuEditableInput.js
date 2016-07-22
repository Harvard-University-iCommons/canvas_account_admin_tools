(function() {
    var app = angular.module('CourseInfo');
    app.directive('huEditableInput', huEditableInput);

    function huEditableInput() {
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
            templateUrl: 'partials/hu-editable-input.html',
        };
    }
})();
