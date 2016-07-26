(function() {
    var app = angular.module('CourseInfo');
    app.directive('huCourseInfoNavTabs', HuCourseInfoNavTabs);

    function HuCourseInfoNavTabs($location) {
        return {
            controller: ['$scope', function($scope) {
                // maps friendly route names to tab indexes
                $scope.routesByName = {
                    details: 0,
                    people: 1,
                    sites: 2
                };
                $scope.activeTabIndex = $scope.routesByName[$scope.currentRoute];
                $scope.getPeopleHeading = function() {
                    switch ($scope.peopleCount) {
                        case undefined:
                            return '<i class="fa fa-refresh fa-spin"></i>' +
                                   ' People';
                        case 1:
                            return '1 Person';
                        default:
                            return $scope.peopleCount + ' People';
                    }
                };
                $scope.getSitesHeading = function() {
                    if (angular.isUndefined($scope.siteCount)) {
                        return '<i class="fa fa-refresh fa-spin"></i>' +
                               ' Associated Sites';
                    }
                    if ($scope.siteCount == 1) {
                        return '1 Associated Site';
                    } else {
                        return $scope.siteCount + ' Associated Sites';
                    }
                };
                $scope.goTo = function(route) {
                    // only execute if not on active tab
                    if ($scope.activeTabIndex == $scope.routesByName[route]) {
                        return;
                    }
                    if (['details', 'people', 'sites'].indexOf(route) > -1) {
                        var url = '/' + route + '/' + $scope.courseInstanceId;
                        $location.path(url);
                    } else {
                        $location.path('/');
                    }
                };
            }],
            restrict: 'E',
            scope: {
                currentRoute: '@',
                courseInstanceId: '<',
                peopleCount: '<',
                siteCount: '<'
            },
            templateUrl: 'partials/hu-course-info-nav-tabs.html'
        };
    }
})();
