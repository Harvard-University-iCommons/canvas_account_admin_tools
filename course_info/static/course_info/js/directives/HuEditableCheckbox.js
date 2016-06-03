(function() {
    var app = angular.module('CourseInfo');
    app.directive('huEditableCheckbox', huEditableCheckbox);

    function huEditableCheckbox() {
        return {
            restrict: 'E',
            scope: {
                editable: '<',  // if not provided, defaults to null/false
                field: '@',
                formValue: '=',
                isLoading: '&',
                label: '@',
                modelValue: '='
            },
            templateUrl: 'partials/hu-editable-checkbox.html',
        };
    }
})();
