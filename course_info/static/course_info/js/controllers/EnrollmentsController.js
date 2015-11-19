(function() {
    var dummyEnrollments = [
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

    var app = angular.module('CourseInfo');
    app.controller('EnrollmentsController', EnrollmentsController);

    function EnrollmentsController($scope, $routeParams, courseInstances, $compile) {
        // TODO - if courseInstances is empty, ajax for the instance details.
        //        needed if someone bookmarks the enrollments view.
        var ci = courseInstances.instances[$routeParams.course_instance_id];

        $scope.course_instance_id = $routeParams.course_instance_id;
        $scope.title = ci ? ci.title : 'NO COURSE INSTANCE FOUND';
        $scope.enrollments = dummyEnrollments;

        $scope.dtOptions = {
            'data': $scope.enrollments,
            'dom': 'rt',
            "createdRow": function( row, data, dataIndex ) {
                $compile(angular.element(row).contents())($scope);
            },
        };
        $scope.dtColumns = [
            {data: 'name', title: 'Name'},
            {
                data: '',
                render: function(data, type, full, meta) {
                    return '<badge role="' + full.role_type_cd + '"></badge> '
                           + full.user_id;
                },
                title: 'ID',
            },
            {data: 'role', title: 'Role'},
            {data: 'source', title: 'Source'},
        ];
    }
})();
