(function() {
    var app = angular.module('CourseInfo');
    app.directive('huEditableTextarea', huEditableTextarea);

    function huEditableTextarea() {
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
            templateUrl: 'partials/hu-editable-textarea.html',
        };
    }
})();
