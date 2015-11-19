(function() {
    var app = angular.module('CourseInfo');
    app.controller('EnrollmentsController', EnrollmentsController);

    function EnrollmentsController($scope, $routeParams, courseInstances, $compile, djangoUrl) {
        // TODO - if courseInstances is empty, ajax for the instance details.
        //        needed if someone bookmarks the enrollments view.
        var ci = courseInstances.instances[$routeParams.course_instance_id];

        $scope.course_instance_id = $routeParams.course_instance_id;
        $scope.title = ci ? ci.title : 'NO COURSE INSTANCE FOUND';
        $scope.dtInstance = null;
        $scope.columnFieldMap = {
            1: 'user__name_last',
            2: 'user__univ_id',
            3: 'role__role_name',
            4: 'source',
        };

        $scope.dtOptions = {
            ajax: function(data, callback, settings) {
                var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                            ['api/course/v2/course_instances/'
                                             + $scope.course_instance_id + '/people/']);
                var queryParams = {
                    offset: data.start,
                    limit: data.length,
                    ordering: (data.order[0].dir === 'desc' ? '-' : '')
                              + $scope.columnFieldMap[data.order[0].column],
                };

                $.ajax({
                    url: url,
                    method: 'GET',
                    data: queryParams,
                    dataType: 'json',
                    success: function(data, textStatus, jqXHR) {
                        callback({
                            recordsTotal: data.count,
                            recordsFiltered: data.count,
                            aaData: data.results,
                        });
                    },
                    error: function(data, textStatus, errorThrown) {
                        console.log('Error getting data from ' + url + ': '
                                    + textStatus + ', ' + errorThrown);
                    },
                });
            },
            createdRow: function( row, data, dataIndex ) {
                $compile(angular.element(row).contents())($scope);
            },
            serverSide: true,
            sAjaxDataProp: 'aaData',
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
})();
