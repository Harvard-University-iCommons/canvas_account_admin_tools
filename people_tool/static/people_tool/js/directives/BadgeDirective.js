(function () {
    var app = angular.module('PeopleTool');

    app.directive('badge', function() {
        return {
            restrict: 'E',
            scope: {
                role: '@',
            },
            controller: function($scope) {

                // get the css class we want for a badge
                $scope.badgeToClassMap = {
                    HUID: 'label-danger',
                    XID: 'label-primary',
                    LIBRARY: 'label-success',
                    OTHER: 'label-warning',
                };
                $scope.badgeToClass = function(badge) {
                    return $scope.badgeToClassMap[badge];
                };
            },
            template: '<span class="label {{ badgeToClass(role) }}">{{ role }}</span>',
        };
    });
})();
