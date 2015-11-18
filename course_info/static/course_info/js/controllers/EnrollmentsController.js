(function() {
    var app = angular.module('CourseInfo');

    app.controller('EnrollmentsController', ['$scope', '$routeParams', 'courseInstances',
        function($scope, $routeParams, courseInstances) {
            // TODO - if courseInstances is empty, ajax for the instance details.
            //        needed if someone bookmarks the enrollments view.
            $scope.course_instance_id = $routeParams.course_instance_id;
            $scope.title = courseInstances.instances[$routeParams.course_instance_id].title;
            $scope.enrollments = [
                {
                    name: 'Brooke, Danny',
                    type: 'HUID',
                    user_id: 987654321,
                    role: 'Guest',
                    source: 'Manually Added',
                },
                {
                    name: 'Bucchieri, Vittorio',
                    type: 'HUID',
                    user_id: 123456789,
                    role: 'Designer',
                    source: 'Manually Added',
                },
                {
                    name: 'Chow, Hiu-Kei',
                    type: 'HUID',
                    user_id: 456789123,
                    role: 'Student',
                    source: 'Registrar Added',
                },
                {
                    name: 'Chow, Hiu-Kei',
                    type: 'XID',
                    user_id: 456789123,
                    role: 'Teaching Assistant',
                    source: 'Manually Added',
                },
                {
                    name: 'Parker, Eric P.',
                    type: 'XID',
                    user_id: 7894567123,
                    role: 'Guest',
                    source: 'Manually Added',
                },
                {
                    name: 'Mysore, Sapna',
                    type: 'HUID',
                    user_id: 456123789,
                    role: 'Teacher',
                    source: 'Manually Added',
                },
                {
                    name: 'Yip, Josie',
                    type: 'HUID',
                    user_id: 789123456,
                    role: 'Teaching Assistant',
                    source: 'Registrar Added',
                },
            ];
        }
    ]);
})();
