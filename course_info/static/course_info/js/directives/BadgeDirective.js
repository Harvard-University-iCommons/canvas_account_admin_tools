(function () {
    var app = angular.module('CourseInfo');

    app.directive('badge', function() {
        return {
            restrict: 'E',
            scope: {
                userType: '@',
                userId: '@',
            },
            controller: function($scope) {
                $scope.typeClasses = {
                    HUID: 'label-danger',
                    XID: 'label-primary',
                }
                $scope.typeClass = function(type) {
                    return $scope.typeClasses[type] || 'label-default';
                };
            },
            templateUrl: 'partials/badge.html',
        };
    });
})();
