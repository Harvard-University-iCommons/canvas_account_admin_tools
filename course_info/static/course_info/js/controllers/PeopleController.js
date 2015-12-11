(function() {
    var app = angular.module('CourseInfo');
    app.controller('PeopleController', PeopleController);

    function PeopleController($scope, $routeParams, courseInstances, $compile, djangoUrl, $http) {
        // set up constants
        $scope.sortKeyByColumnId = {
            0: 'name',
            1: 'user_id',
            2: 'role__role_name',
            3: 'source_manual_registrar',
        };

        // set up functions we'll be calling later
        $scope.ajaxErrorHandler = function(data, status, headers, config) {
            console.log('Error getting data from ' + url + ': '
                        + status + ' ' + data);
        };
        $scope.closeSuccess = function(index) {
            $scope.successes.splice(index, 1);
        };
        $scope.closeWarning = function(index) {
            $scope.warnings.splice(index, 1);
        };
        $scope.isEmailAddress = function(searchTerm) {
            // TODO - better regex
            var re = /^\s*\w+@\w+(\.\w+)+\s*$/;
            return re.test(searchTerm);
        };
        $scope.addUser = function(searchTerm) {
            if ($scope.searchResults.length > 1) {
                // TODO - require that a radio button is checked
                //        (ie. that $scope.selectedResult is valid)
                // TODO - we've already searched and presented a choice of
                // role_type_cd, so just POST the user/role.
            };
            else if ($scope.searchResults === 1) {
                // TODO - shouldn't get here...with a single result, we should
                // just be POSTing.  maybe disable search button while search
                // is in flight?
            }
            else {
                $scope.lookup(searchTerm);
            }
        };
        $scope.lookup = function(searchTerm) {
            // TODO - figure out how to decide if they're already in the class
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                        ['api/course/v2/people/']);
            var params = {page_size: 50};
            if ($scope.isEmailAddress(searchTerm)) {
                params.email_address = searchTerm;
            } else {
                params.univ_id = searchTerm;
            }
            $http.get(url, {params: params})
                .success(function(data, status, headers, config) {
                    // TODO - write generic "follow next link until we exhaust
                    //        the results" code, and use it here
                    $scope.searchResults = data.results;
                    if (data.results.length === 1) {
                        // TODO - POST user, handle results
                    }
                })
                .error($scope.ajaxErrorHandler);
        };
        $scope.renderId = function (data, type, full, meta) {
            return '<badge ng-cloak role="' + full.profile.role_type_cd 
                   + '"></badge> ' + full.user_id;
        };
        $scope.renderName = function (data, type, full, meta) {
            return full.profile.name_last + ', ' + full.profile.name_first;
        };
        $scope.renderSource = function (data, type, full, meta) {
            return /^.*feed$/.test(data) ? 'Registrar Added' : 'Manually Added';
        },
        $scope.setTitle = function(id) {
            var ci = courseInstances.instances[id];
            if (angular.isDefined(ci)) {
                $scope.title = ci.title;
            }
            else {
                $scope.title = '';
                var url = djangoUrl.reverse(
                              'icommons_rest_api_proxy',
                              ['api/course/v2/course_instances/' + id + '/']);
                $http.get(url)
                    .success(function(data, status, headers, config) {
                        courseInstances.instances[data.course_instance_id] = data;
                        $scope.title = data.title;
                    })
                    .error($scope.ajaxErrorHandler);
            }
        };

        // now actually init the controller
        $scope.course_instance_id = $routeParams.course_instance_id;
        $scope.setTitle($scope.course_instance_id);
        $scope.warnings = [
            {search_term: 'foo bar baz'},
            {
                email_address: 'eric_parker@harvard.edu',
                full_name: 'Eric Parker',
                role_type_cd: 'XID',
                enrollments: [{
                    email_address: 'eric_parker@harvard.edu',
                    role_type_cd: 'XID',
                    canvas_role: 'Guest',
                }],
            },
        ];
        $scope.successes = [{
            email_address: 'jill_ehrenzweig@harvard.edu',
            role_type_cd: 'EMPLOYEE',
            univ_id: 123456789,
            canvas_role: 'Teaching Staff',
        }];
        $scope.searchTerm = '';
        $scope.searchResults = [
        /*
            {
                name_last: 'Ehrenzweig',
                name_first: 'Jill',
                email_address: 'jill_ehrenzweig@harvard.edu',
                role_type_cd: 'EMPLOYEE',
                univ_id: 123456789,
            },
            {
                name_last: 'Ehrenzweig',
                name_first: 'Jill',
                email_address: 'jill_ehrenzweig@harvard.edu',
                role_type_cd: 'XID',
                univ_id: 123456789,
            },
            */
        ];
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
                    dataSrc: 'data',
                    dataType: 'json',
                    success: function(data, textStatus, jqXHR) {
                        callback({
                            recordsTotal: data.count,
                            recordsFiltered: data.count,
                            data: data.results,
                        });
                    },
                    error: function(data, textStatus, errorThrown) {
                        console.log('Error getting data from ' + url + ': '
                                    + textStatus + ', ' + errorThrown);
                        callback({
                            recordsTotal: 0,
                            recordsFiltered: 0,
                            data: [],
                        });
                    },
                });
            },
            createdRow: function( row, data, dataIndex ) {
                // to use angular directives within the rendered datatable,
                // we have to compile those elements ourselves.  joy.
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
            // yes, this is a deprecated param.  yes, it's still required.
            // see https://datatables.net/forums/discussion/27287/using-an-ajax-custom-get-function-don-t-forget-to-set-sajaxdataprop
            sAjaxDataProp: 'data',
            searching: false,
            serverSide: true,
        };
        $scope.dtColumns = [
            {
                data: '',
                render: $scope.renderName,
                title: 'Name',
            },
            {
                data: '',
                render: $scope.renderId,
                title: 'ID',
            },
            {data: 'role.role_name', title: 'Role'},
            {
                data: 'source',
                render: $scope.renderSource,
                title: 'Source',
            },
        ];
    }
})();
