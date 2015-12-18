(function() {
    var app = angular.module('CourseInfo');
    app.controller('PeopleController', PeopleController);

    function PeopleController($scope, $routeParams, courseInstances, $compile,
                              djangoUrl, $http, $q) {
        // set up constants
        $scope.sortKeyByColumnId = {
            0: 'name',
            1: 'user_id',
            2: 'role__role_name',
            3: 'source_manual_registrar',
        };

        // set up functions we'll be calling later
        $scope.addUser = function(searchTerm) {
            if ($scope.searchResults.length > 1 && $scope.selectedResult.id) {
                // TODO: assert that radio box is selected
                $scope.addUserToCourse(searchTerm,
                                       {user_id: filteredResults[0].univ_id,
                                        role_id: $scope.selectedRole.roleId});
            }
            else if ($scope.searchResults === 1) {
                // TODO - shouldn't get here, log the error
                console.log('Add user button pressed while we have a single search result');
            }
            else {
                $scope.lookup(searchTerm);
            }
        };
        $scope.addUserToCourse = function(searchTerm, user){
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                        ['api/course/v2/course_instances/'
                                         + $scope.courseInstanceId + '/people/']);
            $http.post(url, user)
                .success(function(data, status, headers, config, statusText) {
                    if (data.detail) {
                        // TODO - put more details into this warning, like
                        //        and user details.
                        $scope.partialFailures.push({
                            searchTerm: searchTerm,
                            text: data.detail,
                        });
                    }

                    $http.get(url, {params: {user_id: user.user_id}})
                        .success(function(data, status, headers, config, statusText) {
                            data.results[0].searchTerm = searchTerm;
                            $scope.successes.push(data.results[0]);
                            $scope.dtInstance.reloadData();
                        })
                        .error(function(data, status, headers, config, statusText) {
                            // log it, then display a warning
                            $scope.handleAjaxError(data, status, headers, config,
                                                   statusText);
                            $scope.partialFailures.push({
                                searchTerm: searchTerm,
                                text: 'Add to course seemed to succeed, but ' +
                                      'we received an error trying to retrieve ' +
                                      "the user's course details.",
                            })
                        });
                })
                .error(function(data, status, headers, config, statusText) {
                    $scope.handleAjaxError(data, status, headers, config, statusText);
                    $scope.warnings.push({
                        type: 'addFailed',
                        searchTerm: searchTerm,
                        roleName: $scope.getRoleName(user.role_id),
                    });
                });
        };
        $scope.closeAlert = function(source, index) {
            $scope[source].splice(index, 1);
        };
        $scope.compareRoles = function(a, b) {
            /*
               concat the active flag with the prime_role_indicator
               value to be able to sort records base on these values
               active = (0 | 1) a value of 1 here trumps the prime_role_indicator
               prime_role_indicator = ( "Y" | "N" | "")
               1 > 0  true
               '1:string' > '0:string' true
               'Y' > 'N' true
               This should let any records with a 1 in the active column float to the top
               if there are non, records with a Y in the prime_role_indicator will float up
               and records with both will float above each of those.
               */
            return b.active == a.active
                ? b.prime_role_indicator > a.prime_role_indicator
                : b.active > a.active;
        };
        $scope.disableAddUserButton = function(){
            if ($scope.searchResults.length > 0 ){
                return (!$scope.selectedResult.id);
            }
            else if ($scope.searchTerm.length > 0){
                return false;
            }
            else {
                return true;
            }
        };
        $scope.filterResults = function(searchResults){
            var filteredResults = Array();
            var resultsDict = {};

            // create a dict of the id's as keys and the
            // role records as values
            for (i = 0; i < searchResults.length; i++) {
                var role = searchResults[i];
                if (resultsDict[role.univ_id] != undefined) {
                    resultsDict[role.univ_id].push(role);
                } else {
                    resultsDict[role.univ_id] = [role];
                }
            }
            // for each id sort the role list
            // and fetch the top record
            for (id in resultsDict) {
                var roleList = resultsDict[id];
                roleList.sort($scope.compareRoles);
                filteredResults.push(roleList[0]);
            }
            // return the filtered list
            return filteredResults;
        };
        $scope.getRoleName = function(roleId) {
            var roles = $scope.roles.filter(
                            function (role) { return role.roleId == roleId; });
            // TODO - error handling if roles.length > 1
            return roles[0].roleName;
        };
        $scope.handleAjaxError = function(data, status, headers, config, statusText) {
            console.log('Error getting data from ' + config.url + ': '
                        + status + ' ' + statusText +
                        ': ' + JSON.stringify(data));
        };
        $scope.handleLookupResults = function(results) {
            var peopleResult = results[0];
            var memberResult = results[1];

            // TODO - implement and use generalized logic that will follow any
            //        "next" links in the rest api response.  note that the api
            //        proxy doesn't rewrite the next urls.
            for (result in results) {
                if (result.next) {
                    console.log('Received multiple pages of results from '
                                + result.config.url + ', only using one.');
                }
            }

            // if the user is already in the course, show their current enrollment
            if (memberResult.data.results.length > 0) {
                // just pick the first one to find the name
                var profile = memberResult.data.results[0].profile
                $scope.warnings.push({
                    type: 'alreadyInCourse',
                    fullName: profile.name_first + ' ' + profile.name_last,
                    memberships: memberResult.data.results,
                    searchTerm: memberResult.config.searchTerm,
                });
            }
            else {
                var filteredResults = $scope.filterResults(
                                          peopleResult.data.results);
                if (filteredResults.length == 0) {
                    // didn't find any people for the search term
                    $scope.warnings.push({
                        type: 'notFound',
                        searchTerm: peopleResult.config.searchTerm,
                    });
                }
                else if (filteredResults.length == 1) {
                    console.log(filteredResults);
                    $scope.addUserToCourse(peopleResult.config.searchTerm,
                                           {user_id: filteredResults[0].univ_id,
                                            role_id: $scope.selectedRole.roleId});
                }
                else {
                    $scope.searchResults = filteredResults;
                }
            }
        };
        $scope.isEmailAddress = function(searchTerm) {
            // TODO - better regex
            var re = /^\s*\w+@\w+(\.\w+)+\s*$/;
            return re.test(searchTerm);
        };
        $scope.lookup = function(searchTerm) {
            // first the general people lookup
            var peopleUrl = djangoUrl.reverse('icommons_rest_api_proxy',
                                              ['api/course/v2/people/']);
            var peopleParams = {page_size: 100};
            if ($scope.isEmailAddress(searchTerm)) {
                peopleParams.email_address = searchTerm;
            } else {
                peopleParams.univ_id = searchTerm;
            }
            var peoplePromise = $http.get(peopleUrl, {params: peopleParams,
                                                      searchTerm: searchTerm})
                                     .error($scope.handleAjaxError);

            // then the course membership lookup
            var memberUrl = djangoUrl.reverse('icommons_rest_api_proxy',
                                              ['api/course/v2/course_instances/'
                                               + $scope.courseInstanceId
                                               + '/people/']);


            var memberParams = {page_size: 100};
            if ($scope.isEmailAddress(searchTerm)) {
                memberParams['profile.email_address'] = searchTerm;
            } else {
                memberParams.user_id = searchTerm;
            }

            var memberPromise = $http.get(memberUrl, {params: memberParams,
                                                      searchTerm: searchTerm})
                                     .error($scope.handleAjaxError);

            // wait until they're both done, handle the combined results
            $q.all([peoplePromise, memberPromise])
                .then($scope.handleLookupResults);
        };
        $scope.renderId = function (data, type, full, meta) {
            return '<badge ng-cloak role="' + full.profile.role_type_cd 
                   + '"></badge> ' + full.user_id;
        };
        $scope.renderName = function (data, type, full, meta) {
            return $scope.getProfileFullName(full.profile);
        };
        $scope.renderSource = function (data, type, full, meta) {
            return /^.*feed$/.test(data) ? 'Registrar Added' : 'Manually Added';
        },
        $scope.selectRole = function (role) {
            $scope.selectedRole = role;
        };
        $scope.setTitle = function (id) {
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
                    .success(function(data, status, headers, config, statusText) {
                        courseInstances.instances[data.course_instance_id] = data;
                        $scope.title = data.title;
                    })
                    .error($scope.handleAjaxError);
            }
        };

        // now actually init the controller
        $scope.courseInstanceId = $routeParams.courseInstanceId;
        $scope.setTitle($scope.courseInstanceId);
        $scope.warnings = [];
        $scope.successes = [];
        $scope.partialFailures = [];
        $scope.searchTerm = '';
        $scope.searchResults = [];
        $scope.selectedResult = {id: undefined};
        $scope.roles = [
            {roleId: 0, roleName: 'Student'},
            {roleId: 10, roleName: 'Guest'},
            {roleId: 14, roleName: 'Shopper'},
            {roleId: 9, roleName: 'Teacher'},
            {roleId: 1, roleName: 'Course Head'},
            {roleId: 2, roleName: 'Faculty'},
            {roleId: 12, roleName: 'Teaching Staff'},
            {roleId: 5, roleName: 'Teaching Fellow'},
            {roleId: 11, roleName: 'Course Support Staff'},
            {roleId: 7, roleName: 'Designer'},
            {roleId: 15, roleName: 'Observer'},
        ];
        $scope.selectedRole = $scope.roles[0];
        $scope.dtInstance = null;
        $scope.dtOptions = {
            ajax: function(data, callback, settings) {
                var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                            ['api/course/v2/course_instances/'
                                             + $scope.courseInstanceId + '/people/']);
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
