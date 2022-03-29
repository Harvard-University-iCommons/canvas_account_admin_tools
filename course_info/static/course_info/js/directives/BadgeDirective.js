(function () {
    var app = angular.module('CourseInfo');

    app.directive('badge', function() {
        return {
            restrict: 'E',
            scope: {
                role: '@',
            },
            controller: function($scope) {
                // convert from role_type_cd to a badge
                $scope.roleToBadgeMap = {
                    CLASPART: 'HUID',
                    COUNTWAY: 'LIBRARY',
                    EMPLOYEE: 'HUID',
                    STUDENT: 'HUID',
                    WIDENER: 'LIBRARY',
                    XIDHOLDER: 'HKL',
                };
                $scope.roleToBadge = function(role) {
                    return $scope.roleToBadgeMap[role] || 'OTHER';
                };

                // get the css class we want for a badge
                $scope.badgeToClassMap = {
                    HUID: 'label-danger',
                    HKL: 'label-primary',
                    LIBRARY: 'label-success',
                    OTHER: 'label-warning',
                }
                $scope.badgeToClass = function(badge) {
                    return $scope.badgeToClassMap[badge];
                };
            },
            template: '<span class="label {{ badgeToClass(roleToBadge(role)) }}">{{ roleToBadge(role) }}</span>',
        };
    });
})();
