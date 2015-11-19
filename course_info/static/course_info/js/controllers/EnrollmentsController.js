(function() {
    var dummyEnrollments = [
        {
            user: {
                name_first: 'Danny',
                name_last: 'Brooke',
                role_type_cd: 'EMPLOYEE',
                univ_id: 987654321,
            },
            role: {
                role_name: 'Guest',
            },
            source: 'peopletool',
        },
        {
            user: {
                name_first: 'Vittorio',
                name_last: 'Bucchieri',
                role_type_cd: 'EMPLOYEE',
                univ_id: 123456789,
            },
            role: {
                role_name: 'Designer',
            },
            source: 'peopletool',
        },
        {
            user: {
                name_first: 'Hiu-Kei',
                name_last: 'Chow',
                role_type_cd: 'EMPLOYEE',
                univ_id: 456789123,
            },
            role: {
                role_name: 'Student',
            },
            source: 'xmlfeed',
        },
        {
            user: {
                name_first: 'Hiu-Kei',
                name_last: 'Chow',
                role_type_cd: 'XIDHOLDER',
                univ_id: 456789123,
            },
            role: {
                role_name: 'Teaching Assistant',
            },
            source: 'peopletool',
        },
        {
            user: {
                name_first: 'Eric P.',
                name_last: 'Parker',
                role_type_cd: 'XIDHOLDER',
                univ_id: 7894567123,
            },
            role: {
                role_name: 'Guest',
            },
            source: 'peopletool',
        },
        {
            user: {
                name_first: 'Sapna',
                name_last: 'Mysore',
                role_type_cd: 'EMPLOYEE',
                univ_id: 456123789,
            },
            role: {
                role_name: 'Teacher',
            },
            source: 'peopletool',
        },
        {
            user: {
                name_first: 'Josie',
                name_last: 'Yip',
                role_type_cd: 'EMPLOYEE',
                univ_id: 789123456,
            },
            role: {
                role_name: 'Teaching Assistant',
            },
            source: 'fasfeed',
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
            {
                data: '',
                render: function(data, type, full, meta) {
                    return full.user.name_last + ', ' + full.user.name_first;
                },
                title: 'Name',
            },
            {
                data: '',
                render: function(data, type, full, meta) {
                    return '<badge role="' + full.user.role_type_cd + '"></badge> '
                           + full.user.univ_id;
                },
                title: 'ID',
            },
            {data: 'role.role_name', title: 'Role'},
            {
                data: 'source',
                render: function(data, type, full, meta) {
                    return (data === 'peopletool')
                               ? 'Manually Added' : 'Registrar Added';
                },
                title: 'Source',
            },
        ];
    }
})();
