(function() {
    var app = angular.module('CourseInfo');
    app.controller('PeopleController', PeopleController);

    function PeopleController($scope, $routeParams, courseInstances, $compile,
                              djangoUrl, $http, $q, $log, $uibModal) {
        // set up constants
        $scope.sortKeyByColumnId = {
            0: 'name',
            1: 'user_id',
            2: 'role__role_name',
            3: 'source_manual_registrar',
        };

        // set up functions we'll be calling later
        $scope.addUser = function(searchTerm) {
            $scope.searchInProgress = true;
            if ($scope.searchResults.length === 0) {
                $scope.lookup(searchTerm);
            }
            else if ($scope.searchResults.length === 1) {
                $log.error('Add user button pressed while we have a single search result');
            }
            else { // $scope.searchResults.length > 1
                if ($scope.selectedResult.id) {
                    $scope.addUserToCourse(searchTerm,
                                           {user_id: $scope.selectedResult.id,
                                            role_id: $scope.selectedRole.roleId});
                }
                else {
                    $scope.lookup(searchTerm);
                }
            }
        };
        $scope.addUserToCourse = function(searchTerm, user){
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                        ['api/course/v2/course_instances/'
                                         + $scope.courseInstanceId + '/people/']);

            // called on actual post success, and on error-but-partial-success
            var handlePostSuccess = function() {
                $http.get(url, {params: {user_id: user.user_id}})
                    .success(function(data, status, headers, config, statusText) {
                        data.results[0].searchTerm = searchTerm;
                        data.results[0].action = 'added to';
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
                        });
                    })
                    .finally(function(){
                        $scope.clearSearchResults();
                        $scope.searchInProgress = false;
                    });
            };

            $http.post(url, user)
                .success(handlePostSuccess)
                .error(function(data, status, headers, config, statusText) {
                    $scope.handleAjaxError(data, status, headers, config, statusText);

                    if (data.detail &&
                            (data.detail.indexOf('Canvas API error details') != -1)) {
                        // partial success, where we enrolled in the coursemanager
                        // db, but got an error trying to enroll in canvas
                        $scope.partialFailures.push({
                            searchTerm: searchTerm,
                            text: data.detail,
                        });
                        handlePostSuccess();
                    }
                    else {
                        $scope.warnings.push({
                            type: 'addFailed',
                            searchTerm: searchTerm,
                        });
                        $scope.clearSearchResults();
                        $scope.searchInProgress = false;
                    }
                });
        };
        $scope.clearSearchResults = function() {
            $scope.searchResults = [];
        };
        $scope.closeAlert = function(source, index) {
            $scope[source].splice(index, 1);
        };
        $scope.compareRoles = function(a, b) {
            /*
             * we want to sort roles by a combination of two fields.
             * - active = (0 | 1)
             * - prime_role_indicator = ('Y' | 'N' | '')
             * 
             * we're sorting descending by active, then descending by
             * prime_role_indicator, where 'Y' > 'N' > ''.
             */
            if (a.active == b.active) {
                if (b.prime_role_indicator > a.prime_role_indicator) {
                    return 1;
                }
                else if (b.prime_role_indicator < a.prime_role_indicator) {
                    return -1;
                }
                else {
                    return 0;
                }
            }
            else {
                return b.active - a.active;
            }
        };
        $scope.confirmRemove = function(membership) {
            // creates a new remove user confirmation modal, and
            // stashes this membership object on the modal's child scope.
            var modalInstance = $uibModal.open({
                controller: function($scope, membership) {
                    $scope.membership = membership;
                },
                resolve: {
                    membership: function() {
                        return membership;
                    },
                },
                templateUrl: 'partials/remove-course-membership-confirmation.html',
            });

            // if they confirm, then do the work
            modalInstance.result.then($scope.removeMembership);
        };
        $scope.disableAddUserButton = function(){
            if ($scope.searchInProgress) {
                return true;
            }
            else if ($scope.searchResults.length > 0) {
                return (!$scope.selectedResult.id);
            }
            else if ($scope.searchTerm.length > 0) {
                return false;
            }
            else {
                return true;
            }
        };
        $scope.filterSearchResults = function(searchResults){
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
        $scope.handleAjaxError = function(data, status, headers, config, statusText) {
            $log.error('Error getting data from ' + config.url + ': ' + status +
                       ' ' + statusText + ': ' + JSON.stringify(data));
        };
        $scope.handleLookupResults = function(results) {
            var peopleResult = results[0];
            var memberResult = results[1];

            // TODO - implement and use generalized logic that will follow any
            //        "next" links in the rest api response.  note that the api
            //        proxy doesn't rewrite the next urls.
            for (result in results) {
                if (result.next) {
                    $log.warning('Received multiple pages of results from '
                                 + result.config.url + ', only using one.');
                }
            }

            // if the user is already in the course, show their current enrollment
            if (memberResult.data.results.length > 0) {
                // just pick the first one to find the name
                var profile = memberResult.data.results[0].profile
                $scope.warnings.push({
                    type: 'alreadyInCourse',
                    fullName: profile.name_last + ', ' + profile.name_first,
                    memberships: memberResult.data.results,
                    searchTerm: memberResult.config.searchTerm,
                });
                $scope.searchInProgress = false;
            }
            else {
                var filteredResults = $scope.filterSearchResults(
                                          peopleResult.data.results);
                if (filteredResults.length == 0) {
                    // didn't find any people for the search term
                    $scope.warnings.push({
                        type: 'notFound',
                        searchTerm: peopleResult.config.searchTerm,
                    });
                    $scope.searchInProgress = false;
                }
                else if (filteredResults.length == 1) {
                    $scope.addUserToCourse(peopleResult.config.searchTerm,
                                           {user_id: filteredResults[0].univ_id,
                                            role_id: $scope.selectedRole.roleId});
                }
                else {
                    $scope.searchResults = filteredResults;
                    $scope.searchInProgress = false;
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
            var peopleURL = djangoUrl.reverse('icommons_rest_api_proxy',
                                              ['api/course/v2/people/']);
            var peopleParams = {page_size: 100};
            if ($scope.isEmailAddress(searchTerm)) {
                peopleParams.email_address = searchTerm;
            } else {
                peopleParams.univ_id = searchTerm;
            }
            var peoplePromise = $http.get(peopleURL, {params: peopleParams,
                                                      searchTerm: searchTerm})
                                     .error($scope.handleAjaxError);

            // then the course membership lookup
            var memberURL = djangoUrl.reverse('icommons_rest_api_proxy',
                                              ['api/course/v2/course_instances/'
                                               + $scope.courseInstanceId
                                               + '/people/']);


            var memberParams = {page_size: 100};
            if ($scope.isEmailAddress(searchTerm)) {
                memberParams['profile.email_address'] = searchTerm;
            } else {
                memberParams.user_id = searchTerm;
            }

            var memberPromise = $http.get(memberURL, {params: memberParams,
                                                      searchTerm: searchTerm})
                                     .error($scope.handleAjaxError);

            // wait until they're both done, handle the combined results
            $q.all([peoplePromise, memberPromise])
                .then($scope.handleLookupResults);
        };
        $scope.removeMembership = function(membership) {
            // the call stack to get here is a little weird.  we register
            // this as the success callback on a promise hung off the
            // $uibModal instance.
            var courseMemberURL = djangoUrl.reverse(
                                      'icommons_rest_api_proxy',
                                      ['api/course/v2/course_instances/' +
                                       $scope.courseInstanceId +
                                       '/people/' + membership.user_id]);
            var config = {
                data: {
                    role_id: membership.role.role_id,
                    user_id: membership.user_id,
                },
                headers: {
                    'Content-Type': 'application/json',
                },
            };
            $http.delete(courseMemberURL, config)
                 .success(function() {
                     var success = membership; // TODO - copy to avoid stomping the original?
                     success.searchTerm = membership.user_id;
                     success.action = 'removed from';
                     $scope.successes.push(success);
                     $scope.dtInstance.reloadData()
                 })
                 .error($scope.handleAjaxError) // TODO - real error handling
                 ;
        };
        $scope.renderId = function(data, type, full, meta) {
            return '<badge ng-cloak role="' + full.profile.role_type_cd 
                   + '"></badge> ' + full.user_id;
        };
        $scope.renderName = function(data, type, full, meta) {
            return full.profile.name_last + ', ' + full.profile.name_first;
        };
        $scope.renderRemove = function(data, type, full, meta) {
            // TODO - maybe make this a directive?  the isolate scope
            //        in a directive complicates things.  anything has
            //        to be better than this mess, though.
            var registrarFed = /^.*feed$/.test(full.source);
            var cell = '<div class="text-center">';
            if (!registrarFed) {
                cell += '<a href="" ng-click="confirmRemove(' +
                        'dtInstance.DataTable.data()[' + meta.row + '])">';
            }
            cell += '<i class="fa fa-trash-o"';
            if (registrarFed) {
                cell += ' style="color: #ccc;"';
            }
            cell += '></i>';
            if (!registrarFed) {
                cell += '</a>';
            }
            cell += '</div>';
            return cell;
        }
        $scope.renderSource = function(data, type, full, meta) {
            return /^.*feed$/.test(data) ? 'Registrar Added' : 'Manually Added';
        };
        $scope.selectRole = function(role) {
            $scope.selectedRole = role;
        };
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
                    .success(function(data, status, headers, config, statusText) {
                        courseInstances.instances[data.course_instance_id] = data;
                        $scope.title = data.title;
                    })
                    .error($scope.handleAjaxError);
            }
        };

        // now actually init the controller
        $scope.courseInstanceId = $routeParams.courseInstanceId;
        $scope.partialFailures = [];
        $scope.roles = [
            // NOTE - these may need to be updated based on the db values
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
        $scope.searchInProgress = false;
        $scope.searchResults = [];
        $scope.searchTerm = '';
        $scope.selectedResult = {id: undefined};
        $scope.selectedRole = $scope.roles[0];
        $scope.setTitle($routeParams.courseInstanceId);
        $scope.successes = [];
        $scope.warnings = [];

        // configure the datatable
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
                        $log.error('Error getting data from ' + url + ': '
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
            {
                data: '',
                render: $scope.renderRemove,
                title: 'Remove',
                // TODO - flag as not sortable
            },
        ];
    }
})();
