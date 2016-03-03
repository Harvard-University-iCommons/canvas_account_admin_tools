// TODO - split out add/remove into separate controllers?
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
            $scope.clearMessages();
            $scope.partialFailureData = null;

            // called on actual post success, and on error-but-partial-success
            var handlePostSuccess = function() {
                $http.get(url, {params: {user_id: user.user_id}})
                    .success(function(data, status, headers, config, statusText) {

                        // this is a temp fix to change the display text of the role "Teaching Fellow" to "TA"
                        // a more perm solution is being discussed, but will invlove talking to the schools.
                        if ( data.results[0].role.role_name == "Teaching Fellow") {
                            data.results[0].role.role_name = "TA";
                        }

                        data.results[0].searchTerm = searchTerm;
                        data.results[0].action = 'added to';
                        $scope.clearMessages();
                        // if there was a partial error, specifically if there was
                        // an error adding the user to the Canvas course (we caught
                        // a Canvas API error). The user has been added to the
                        // coursemanager db, but could not be added to Canvas.
                        // In this case it's possible that the user will be addded
                        // during the next Canvas sync. We let the user know about
                        // the partial failure and that it may correct itself.
                        if($scope.partialFailureData){
                            data.results[0].partialFailureData = $scope.partialFailureData
                        }

                        $scope.success = data.results[0];
                        $scope.dtInstance.reloadData();
                    })
                    .error(function(data, status, headers, config, statusText) {
                        // log it, then display a warning
                        $scope.handleAjaxError(data, status, headers, config,
                                statusText);
                        $scope.clearMessages();
                        $scope.addPartialFailure = {
                            searchTerm: searchTerm,
                            text: 'Add to course seemed to succeed, but ' +
                                'we received an error trying to retrieve ' +
                                "the user's course details.",
                        };
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
                        $scope.partialFailureData = {
                            searchTerm: searchTerm,
                            text: data.detail
                        };
                        handlePostSuccess();
                    }
                    else {
                        $scope.clearMessages();
                        $scope.addWarning = {
                            type: 'addFailed',
                            searchTerm: searchTerm,
                        };
                        $scope.clearSearchResults();
                        $scope.searchInProgress = false;
                    }
                });
        };
        $scope.clearSearchResults = function() {
            $scope.searchResults = [];
        };
        $scope.closeAlert = function(source) {
            $scope[source] = null;
            $scope.partialFailureData = null;
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

            // this is a temp fix to change the display text of the role "Teaching Fellow" to "TA"
            // a more perm solution is being discussed, but will invlove talking to the schools.
            if (membership && membership.role &&
                    membership.role.role_name == "Teaching Fellow") {
                membership.role.role_name = "TA";
            }

            $scope.confirmRemoveModalInstance = $uibModal.open({
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
            $scope.confirmRemoveModalInstance.result
                .then($scope.removeMembership)
                .finally(function() {
                    $scope.confirmRemoveModalInstance = null;
                });
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
        $scope.getProfileFullName = function(profile) {
            if (profile) {
                return profile.name_last + ', ' + profile.name_first;
            } else {
                return '';
            }
        };
        $scope.getProfileRoleTypeCd = function (profile) {
            if (profile) {
                return profile.role_type_cd;
            } else {
                return '';
            }
        };
        $scope.handleAjaxError = function(data, status, headers, config, statusText) {
            $log.error('Error attempting to ' + config.method + ' ' + config.url +
                       ': ' + status + ' ' + statusText + ': ' + JSON.stringify(data));
        };
        $scope.handleLookupResults = function(results) {
            var peopleResult = results[0];
            var memberResult = results[1];

            // this is a temp fix to change the display text of the role "Teaching Fellow" to "TA"
            // a more perm solution is being discussed, but will invlove talking to the schools.
            if (memberResult.data.results.length > 0 &&
                    memberResult.data.results[0].role &&
                    memberResult.data.results[0].role.role_name == "Teaching Fellow") {
                memberResult.data.results[0].role.role_name = "TA";
            }

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
                var profile = memberResult.data.results[0].profile;
                $scope.clearMessages();
                $scope.addWarning = {
                    type: 'alreadyInCourse',
                    fullName: $scope.getProfileFullName(profile),
                    memberships: memberResult.data.results,
                    searchTerm: memberResult.config.searchTerm,
                };
                $scope.searchInProgress = false;
            }
            else {
                var filteredResults = $scope.filterSearchResults(
                                          peopleResult.data.results);
                if (filteredResults.length == 0) {
                    // didn't find any people for the search term
                    $scope.clearMessages();
                    $scope.addWarning = {
                        type: 'notFound',
                        searchTerm: peopleResult.config.searchTerm,
                    };
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
                .success(function(data, status, headers, config, statusText) {
                    var success = membership; // TODO - copy to avoid stomping the original?
                    success.searchTerm = $scope.getProfileFullName(membership.profile)
                        || membership.user_id;
                    success.action = 'removed from';
                    $scope.clearMessages();
                    $scope.success = success;
                    $scope.dtInstance.reloadData()
                })
                .error(function(data, status, headers, config, statusText) {
                    $scope.handleAjaxError(data, status, headers, config, statusText);

                    var failure = membership; // TODO - copy to avoid stomping the original?
                    var reloadData = false; // for some partial failures we need to reload
                    switch(status) {
                        case 404:
                            switch (data.detail) {
                                case 'User not found.':
                                    failure.type = 'noSuchUser';
                                    reloadData = true;
                                    break;
                                case 'Course instance not found.':
                                    failure.type = 'noSuchCourse';
                                    break;
                                default:
                                    failure.type = 'unexpected404';
                                    break;
                            }
                            break;

                        case 500:
                            if (data.detail == 'User could not be removed from Canvas.') {
                                failure.type = 'canvasError';
                                reloadData = true;
                            }
                            else {
                                failure.type = 'serverError';
                            }
                            break;

                        default:
                            failure.type = 'unknown';
                            break;
                    }
                    $scope.clearMessages();
                    $scope.removeFailure = failure;
                    if (reloadData) {
                        $scope.dtInstance.reloadData();
                    }
                });
        };
        $scope.renderId = function(data, type, full, meta) {
            if (full.profile) {
                return '<badge ng-cloak role="'
                    + $scope.getProfileRoleTypeCd(full.profile)
                    + '"></badge> ' + full.user_id;
            } else {
                return '<badge ng-cloak role=""></badge> ' + full.user_id;
            }
        };
        $scope.renderName = function(data, type, full, meta) {
            return $scope.getProfileFullName(full.profile) || full.user_id;
        };
        // hotfix added to address TA role name
        // will be addressed with a database change as soon as
        // devops determines viability of change
        $scope.renderRole = function(data, type, full, meta) {
            return /^Teaching Fellow$/.test(data) ? 'TA' : data;
        };
        $scope.renderRemove = function(data, type, full, meta) {
            // TODO - maybe make this a directive?  the isolate scope
            //        in a directive complicates things.  anything has
            //        to be better than this mess, though.
            var registrarFed = /^.*feed$/.test(full.source);
            var iconClass = registrarFed ? 'fa-trash-disabled' : '';
            var icon = '<i class="fa fa-trash-o ' + iconClass + '"></i>';
            var linkOpen = '';
            if (!registrarFed) {
                linkOpen = '<a href="" ng-click="confirmRemove(' +
                           'dtInstance.DataTable.data()[' + meta.row + '])" ' +
                           'data-sisid="' + full.user_id + '">';
            }
            var linkClose = registrarFed ? '' : '</a>';
            return '<div class="text-center">' +
                       linkOpen + icon + linkClose + '</div>';
        }
        $scope.renderSource = function(data, type, full, meta) {
            return /^.*feed$/.test(data) ? 'Registrar Added' : 'Manually Added';
        };
        $scope.selectRole = function(role) {
            $scope.selectedRole = role;
        };
        $scope.setCourseInstance = function(id) {
            var ci = courseInstances.instances[id];
            if (angular.isDefined(ci)) {
                $scope.courseInstance = $scope.getFormattedCourseInstance(ci)
            }
            else {
                var url = djangoUrl.reverse(
                              'icommons_rest_api_proxy',
                              ['api/course/v2/course_instances/' + id + '/']);
                $http.get(url)
                    .success(function(data, status, headers, config, statusText) {
                        //check if the right data was obtained before storing it
                        if (data.course_instance_id == id){
                            courseInstances.instances[data.course_instance_id] = data;
                            $scope.courseInstance = $scope.getFormattedCourseInstance(data)
                        }else{
                            $log.error(' CourseInstance record mismatch for id :'
                                + id +',  fetched record for :' +data.id);
                        }
                    })
                    .error($scope.handleAjaxError);
            }
        };

        $scope.getFormattedCourseInstance = function(ci) {
            // This is a helper function that formats the CourseInstance metadata
            // and is combination of existing logic in
            // Searchcontroller.courseInstanceToTable and Searchcontroller cell
            // render functions.
            courseInstance = {};
            if (ci) {
                courseInstance['title']= ci.title;
                courseInstance['school'] = ci.course ?
                        ci.course.school_id.toUpperCase() : '';
                courseInstance['term'] = ci.term ? ci.term.display_name : '';
                courseInstance['year'] = ci.term ? ci.term.academic_year : '';
                courseInstance['cid'] = ci.course_instance_id;
                courseInstance['registrar_code_display'] = ci.course ?
                        ci.course.registrar_code_display +
                        ' (' + ci.course.course_id + ')'.trim() : '';
                if (ci.secondary_xlist_instances &&
                    ci.secondary_xlist_instances.length > 0) {
                        courseInstance['xlist_status'] = 'Primary';
                } else if (ci.primary_xlist_instances &&
                    ci.primary_xlist_instances.length > 0) {
                        courseInstance['xlist_status'] = 'Secondary';
                } else {
                        courseInstance['xlist_status'] = 'N/A';
                }
                var sites = ci.sites || [];
                var siteIds =[]
                sites.forEach(function (site) {
                    site.site_id = site.external_id;
                    if (site.site_id.indexOf('http') === 0) {
                        site.site_id = site.site_id.substr(site.site_id.lastIndexOf('/')+1);
                    }
                    siteIds.push(site.site_id)
                });
                courseInstance['sites']= siteIds.length>0 ? siteIds.join(', ') : 'N/A';
            }
            return courseInstance;
        };

        $scope.clearMessages = function(){
            $scope.addPartialFailure = null;
            $scope.removeFailure = null;
            $scope.addWarning = null;
            $scope.success = null;
        };

        // now actually init the controller
        $scope.addPartialFailure = null;
        $scope.partialFailureData = null;
        $scope.addWarning = null;
        $scope.confirmRemoveModalInstance = null;
        $scope.courseInstanceId = $routeParams.courseInstanceId;
        $scope.removeFailure = null;

        $scope.roles = [
            // NOTE - these may need to be updated based on the db values
            {roleId: 0, roleName: 'Student'},
            {roleId: 10, roleName: 'Guest'},
            {roleId: 14, roleName: 'Shopper'},
            {roleId: 9, roleName: 'Teacher'},
            {roleId: 1, roleName: 'Course Head'},
            {roleId: 2, roleName: 'Faculty'},
            {roleId: 12, roleName: 'Teaching Staff'},
            {roleId: 5, roleName: 'TA'},
            {roleId: 11, roleName: 'Course Support Staff'},
            {roleId: 7, roleName: 'Designer'},
            {roleId: 15, roleName: 'Observer'},
        ];
        $scope.searchInProgress = false;
        $scope.searchResults = [];
        $scope.searchTerm = '';
        $scope.selectedResult = {id: undefined};
        $scope.selectedRole = $scope.roles[0];
        $scope.setCourseInstance($routeParams.courseInstanceId);
        $scope.success = null;

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
            lengthMenu: [10, 25, 50, 100],
            // yes, this is a deprecated param.  yes, it's still required.
            // see https://datatables.net/forums/discussion/27287/using-an-ajax-custom-get-function-don-t-forget-to-set-sajaxdataprop
            sAjaxDataProp: 'data',
            searching: false,
            serverSide: true,
        };

        // see hotfix note above for renderRole
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
            {
                data: 'role.role_name',
                render: $scope.renderRole,
                title: 'Role'
            },
            {
                data: 'source',
                render: $scope.renderSource,
                title: 'Source',
            },
            {
                data: '',
                orderable: false,
                render: $scope.renderRemove,
                title: 'Remove',
            },
        ];
    }
})();
