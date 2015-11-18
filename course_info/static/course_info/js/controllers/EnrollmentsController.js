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
                    role_type_cd: 'EMPLOYEE',
                    user_id: 987654321,
                    role: 'Guest',
                    source: 'Manually Added',
                },
                {
                    name: 'Bucchieri, Vittorio',
                    role_type_cd: 'EMPLOYEE',
                    user_id: 123456789,
                    role: 'Designer',
                    source: 'Manually Added',
                },
                {
                    name: 'Chow, Hiu-Kei',
                    role_type_cd: 'EMPLOYEE',
                    user_id: 456789123,
                    role: 'Student',
                    source: 'Registrar Added',
                },
                {
                    name: 'Chow, Hiu-Kei',
                    role_type_cd: 'XIDHOLDER',
                    user_id: 456789123,
                    role: 'Teaching Assistant',
                    source: 'Manually Added',
                },
                {
                    name: 'Parker, Eric P.',
                    role_type_cd: 'XIDHOLDER',
                    user_id: 7894567123,
                    role: 'Guest',
                    source: 'Manually Added',
                },
                {
                    name: 'Mysore, Sapna',
                    role_type_cd: 'EMPLOYEE',
                    user_id: 456123789,
                    role: 'Teacher',
                    source: 'Manually Added',
                },
                {
                    name: 'Yip, Josie',
                    role_type_cd: 'EMPLOYEE',
                    user_id: 789123456,
                    role: 'Teaching Assistant',
                    source: 'Registrar Added',
                },
            ];
        }
    ]);
})();
