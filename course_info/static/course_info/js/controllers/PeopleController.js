(function() {
    var app = angular.module('CourseInfo');
    app.controller('PeopleController', PeopleController);

    function PeopleController($scope, $routeParams, courseInstances, $compile, djangoUrl) {
        $scope.course_instance_id = $routeParams.course_instance_id;
        var ci = courseInstances.instances[$scope.course_instance_id];
        if (angular.isDefined(ci)) {
            $scope.title = ci.title;
        }
        else {
            $scope.title = '';
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                        ['api/course/v2/course_instances/'
                                         + $scope.course_instance_id + '/']);
            $.ajax({
                url: url,
                dataType: 'json',
                success: function(data, textStatus, jqXHR) {
                    $scope.$apply(function(){
                        $scope.title = data.title;
                        courseInstances.instances[data.course_instance_id] = data;
                    });
                },
                error: function(data, textStatus, errorThrown) {
                    console.log('Error getting data from ' + url + ': '
                                + textStatus + ', ' + errorThrown);
                },
            });
        }

        $scope.sortKeyByColumnId = {
            0: 'name',
            1: 'user_id',
            2: 'role__role_name',
            3: 'source_manual_registrar',
        };
        $scope.dtInstance = null;  // not used in code, useful for debugging
        $scope.dtOptions = {
            ajax: function(data, callback, settings) {
                var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                            ['api/course/v2/course_instances/'
                                             + $scope.course_instance_id + '/people/']);
                var queryParams = {
                    offset: data.start,
                    limit: data.length,
                    '-source': 'xreg_map', // exclude xreg people
                    ordering: (data.order[0].dir === 'desc' ? '-' : '')
                              + $scope.sortKeyByColumnId[data.order[0].column],
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
                        callback({
                            recordsTotal: 0,
                            recordsFiltered: 0,
                            aaData: [],
                        });
                    },
                });
            },
            createdRow: function( row, data, dataIndex ) {
                $compile(angular.element(row).contents())($scope);
            },
            language: {
                emptyTable: 'There are no people to display.',
                info: 'Showing _START_ to _END_ of _TOTAL_ people',
                infoEmpty: 'Showing 0 to 0 of 0 people',
                paginate: {
                    next: '',
                    previous: '',
                },
            },
            lengthChange: false,
            sAjaxDataProp: 'aaData',
            searching: false,
            serverSide: true,
        };
        $scope.dtColumns = [
            {
                data: '',
                render: function(data, type, full, meta) {
                    return full.profile.name_last + ', ' + full.profile.name_first;
                },
                title: 'Name',
            },
            {
                data: '',
                render: function(data, type, full, meta) {
                    return '<badge ng-cloak role="' + full.profile.role_type_cd + '"></badge> '
                           + full.user_id;
                },
                title: 'ID',
            },
            {data: 'role.role_name', title: 'Role'},
            {
                data: 'source',
                render: function(data, type, full, meta) {
                    return /^(|.*feed)$/.test(data) ? 'Registrar Added' : 'Manually Added';
                },
                title: 'Source',},
        ];
    }
})();
