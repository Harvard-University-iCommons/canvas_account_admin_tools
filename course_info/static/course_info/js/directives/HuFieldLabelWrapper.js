(function() {
    var app = angular.module('CourseInfo');
    app.directive('huFieldLabelWrapper', huFieldLabelWrapper);

    function huFieldLabelWrapper() {
        return {
            scope: {
                field: '@',
                isLoading: '&',
                label: '@'
            },
            templateUrl: 'partials/hu-field-label-wrapper.html',
            transclude: true,
        };
    }
})();
