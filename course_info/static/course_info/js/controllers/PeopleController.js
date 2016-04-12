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
        $scope.addNewMember = function(personResponse, members) {
            /* Make a call to add the person to the course as a new member
             if person is:
             - not already in `members`
             - not found in people lookup
             - represented by more than one profile
             Returns a promise representing the call made to add the new member
             to the course, or null if the add was not attempted for one of the
             reasons listed above.
             */
            // TODO - implement and use generalized logic that will follow any
            //        "next" links in the rest api response.  note that the api
            //        proxy doesn't rewrite the next urls.
            if (personResponse.next) {
                $log.warning('Received multiple pages of results from '
                             + personResponse.config.url + ', only using one.');
            }

            var filteredResults = $scope.filterSearchResults(
                                      personResponse.data.results);
            var searchTerm = personResponse.config.searchTerm;
            if (filteredResults.length == 1) {
                var memberRecordsInCourse = members[filteredResults[0].univ_id];
                if (angular.isUndefined(memberRecordsInCourse)) {
                    var name = $scope.getProfileFullName(filteredResults[0]);
                    var postParams = {
                        user_id: filteredResults[0].univ_id,
                        role_id: $scope.selectedRole.roleId};
                    return $scope.addNewMemberToCourse(postParams, name,
                            searchTerm);
                } else {
                    // the user already has an enrollment in the course
                    $scope.messages.warnings.push({
                        type: 'alreadyInCourse',
                        // just pick the first enrollment to find the name
                        name: $scope.getProfileFullName(filteredResults[0]),
                        memberships: memberRecordsInCourse,
                        searchTerm: searchTerm
                    });
                    $scope.tracking.failures  += 1;
                }
            } else if (filteredResults.length == 0) {
                // didn't find any people for the search term
                $scope.messages.warnings.push({
                    type: 'notFound',
                    searchTerm: searchTerm
                });
                $scope.tracking.failures  += 1;
            } else {  // if (filteredResults.length > 1)
                // multiple profiles found for search term, do not add
                $scope.messages.warnings.push({
                    type: 'multipleProfiles',
                    searchTerm: personResponse.config.searchTerm,
                    // just pick the first one to find the name
                    name: $scope.getProfileFullName(filteredResults[0]),
                    profiles: filteredResults
                });
                $scope.tracking.failures  += 1;
            }
            $scope.updateProgressBar();  // handles failures
            // todo: do we need to return a resolved or rejected promise here instead?
            return null;  // no attempt made to add member
        };
        $scope.addNewMemberToCourse = function(userPostParams, userName,
                                               searchTerm) {
            /* Adds a single person to the course; handles the actual posting of
             member info to the course via the API. Returns a promise for the
             POST call response.
             */
            var handlePostSuccess = function(response) {
                $scope.tracking.successes += 1;
                $scope.updateProgressBar();
                return response;
            };

            var handlePostError = function(response) {
                $scope.handleAjaxErrorResponse(response);
                if (response.data.detail &&
                        (response.data.detail.indexOf(
                            'Canvas API error details') != -1)) {
                    // There was a partial error (we caught
                    // a Canvas API error). The user has been added to the
                    // coursemanager db, but could not be added to Canvas.
                    // In this case it's possible that the user will be added
                    // during the next Canvas sync. We let the user know about
                    // the partial failure and that it may correct itself.
                    $scope.messages.warnings.push({
                        type: 'partialFailure',
                        failureDetail: response.data.detail,
                        name: userName,
                        searchTerm: searchTerm
                    });
                }
                else {
                    $scope.messages.warnings.push({
                        type: 'addFailed',
                        name: userName,
                        searchTerm: searchTerm
                    });
                }
                $scope.tracking.failures  += 1;
                $scope.updateProgressBar();
                return response;
            };

            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                        ['api/course/v2/course_instances/'
                                         + $scope.courseInstanceId + '/people/']);

            return $http.post(url, userPostParams)
                .then(handlePostSuccess, handlePostError);
        };
        $scope.addPeopleToCourse = function(searchTerms) {
            /* looks up HUIDs, XIDs, and/or email addresses from searchTerms
             and attempts to add people to the course who do not already have an
             enrollment.
             */
            var membersByUserId = {};
            $scope.clearMessages();
            $scope.operationInProgress = true;
            var searchTermList = $scope.getSearchTermList(searchTerms);
            $scope.tracking.total = searchTermList.length;
            $scope.updateProgressBar('Looking up ' + $scope.tracking.total
                + ' people');
            var memberPromise = $scope.lookupCourseMembers()
                .then(function updateCourseMembers(memberResponse) {
                    membersByUserId = $scope.getMembersByUserId(
                        memberResponse.data.results);
                    return memberResponse;
                }, function courseMemberLookupFailed(memberResponse) {
                    $scope.handleAjaxErrorResponse(memberResponse);
                    // todo: how do we make this break the add chain?
                    return $q.reject('Course member lookup failed');
                });
            var peoplePromises = $scope.lookupPeople(searchTermList);
            var addNewMemberPromises = [];
            peoplePromises.forEach(function setupAddPersonPromiseChain(personPromise) {
                addNewMemberPromises.push(
                    $q.all([memberPromise, personPromise])
                        .then(function addFetchedPerson(responses) {
                            var personResponse = responses[1];
                            $scope.updateProgressBar();
                            return $scope.addNewMember(personResponse, membersByUserId);
                        })
                    );
                });
            $q.all(addNewMemberPromises).then($scope.showAddNewMemberResults);

        };
        $scope.clearMessages = function() {
            $scope.messages = {progress: null, success: null, warnings: []};
            $scope.tracking = {
                failures: 0,
                successes: 0,
                lookupsCompleted: 0,
                total: 0};
            $scope.removeFailure = null;
        };
        $scope.closeAlert = function(source) {
            $scope.messages[source] = null;
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
                    }
                },
                // allows template to refer to parent scope's getProfileFullName
                scope: $scope,
                templateUrl: 'partials/remove-course-membership-confirmation.html',
            });

            // if they confirm, then do the work
            $scope.confirmRemoveModalInstance.result
                .then(
                    function modalSuccess(membership) {
                        $scope.removeMembership(membership);
                    },
                    function modalFailure(failure) {
                        $log.error('remove confirmation modal failure: ' + failure);
                    }
                )
                .finally(function() {
                    $scope.confirmRemoveModalInstance = null;
                });
        };
        $scope.disableAddToCourseButton = function(){
            return ($scope.operationInProgress || $scope.searchTerms.length == 0);
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
        $scope.getFormattedCourseInstance = function(ci) {
            // This is a helper function that formats the CourseInstance metadata
            // and is combination of existing logic in
            // Searchcontroller.courseInstanceToTable and Searchcontroller cell
            // render functions.
            var courseInstance = {};
            if (ci) {
                courseInstance['title']= ci.title;
                courseInstance['school'] = ci.course ?
                        ci.course.school_id.toUpperCase() : '';
                courseInstance['term'] = ci.term ? ci.term.display_name : '';
                courseInstance['year'] = ci.term ? ci.term.academic_year : '';
                courseInstance['course_instance_id'] = ci.course_instance_id;
                courseInstance['registrar_code_display'] = ci.course ?
                        (ci.course.registrar_code_display
                        || ci.course.registrar_code).trim() : '';
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
                var siteIds =[];
                sites.forEach(function (site) {
                    site.site_id = site.external_id;
                    if (site.site_id.indexOf('http') === 0) {
                        site.site_id = site.site_id.substr(site.site_id.lastIndexOf('/')+1);
                    }
                    siteIds.push(site.site_id);
                });
                courseInstance['sites']= siteIds.length>0 ? siteIds.join(', ') : 'N/A';
            }
            return courseInstance;
        };
        $scope.getMembersByUserId = function(memberList) {
            /* generates a lookup table/dict/object to find a member's profile
             by univ_id; used e.g. for checking whether the univ_id found for
             each person in the search term lookup results is already in the
             course or not
             */
            var membersByUserId = {};
            memberList.forEach(function(member) {
                var memberCopy = angular.copy(member);
                // this is a temp fix to change the display text of the role
                // "Teaching Fellow" to "TA" a more perm solution is being
                // discussed, but will involve talking to the schools.
                if (member.role && member.role.role_name == "Teaching Fellow") {
                    memberCopy.role.role_name = "TA";
                }
                membersByUserId[member.user_id] =
                    (membersByUserId[member.user_id] || []).push(memberCopy);
            });
            return membersByUserId;
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
        $scope.getSearchTermList = function(searchTerms) {
            // search terms input (string) split by commas, newlines into array
            return searchTerms.split(new RegExp('\n|,', 'g'))
                .map(function(s){return s.trim()})
                .filter(function(s){return s.length});
        };
        $scope.handleAjaxError = function(data, status, headers, config, statusText) {
            $log.error('Error attempting to ' + config.method + ' ' + config.url +
                       ': ' + status + ' ' + statusText + ': ' + JSON.stringify(data));
        };
        $scope.handleAjaxErrorResponse = function(r) {
            // angular promise then() function returns a response object,
            // unpack for our old-style error handler
            $scope.handleAjaxError(
                r.data, r.status, r.headers, r.config, r.statusText);
        };
        $scope.isUnivID = function(searchTerm) {
            var re = /^[A-Za-z0-9]{8}$/;
            return re.test(searchTerm);
        };
        $scope.lookupCourseMembers = function() {
            // todo: this needs to support unlimited pages; see TLT-2267
            // exclude xreg people
            var getConfig = {
                params: {limit: 100, '-source': 'xreg_map'}};
            var memberURL = djangoUrl.reverse('icommons_rest_api_proxy',
                                              ['api/course/v2/course_instances/'
                                               + $scope.courseInstanceId
                                               + '/people/']);
            return $http.get(memberURL, getConfig);
        };
        $scope.lookupPeople = function(searchTermList) {
            /* generates a list of promises (http requests to the API) for the
              search terms provided in order to get the univ_id for each
              person the user wants to add
              */
            var peopleURL = djangoUrl.reverse('icommons_rest_api_proxy',
                                              ['api/course/v2/people/']);
            var peoplePromiseList = [];

            searchTermList.forEach(function(searchTerm) {
                var promiseConfig = {
                    params: {limit: 100},
                    searchTerm: searchTerm  // save for error handling
                };
                if ($scope.isUnivID(searchTerm)) {
                    promiseConfig.params.univ_id = searchTerm;
                } else {
                    promiseConfig.params.email_address = searchTerm;
                }
                var promise = $http.get(peopleURL, promiseConfig)
                    .then(function(response) {
                        $scope.tracking.lookupsCompleted += 1;
                        return response;
                    });
                peoplePromiseList.push(promise);
            });

            return peoplePromiseList;
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
                    // make profile available to template for success message
                    var success = angular.copy(membership);
                    success.searchTerm = $scope.getProfileFullName(membership.profile)
                        || membership.user_id;
                    success.type = 'remove';
                    success.alertType = 'success';
                    $scope.clearMessages();
                    $scope.messages.success = success;
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
        $scope.showAddNewMemberResults = function(addNewMemberResponses) {
            /* Updates page with summary message and failure details after all
             add person operations are finished.
             */
            $scope.operationInProgress = false;
            // use 'total_failures' to avoid stomping existing 'failures'
            $scope.tracking.total_failures = $scope.tracking.total - $scope.tracking.successes;
            // figure out the alert type (ie. the color) here
            var alertType = '';
            if ($scope.tracking.successes == 0) {
                alertType = 'danger';
            }
            else if ($scope.tracking.total_failures == 0) {
                alertType = 'success';
            }
            else {
                alertType = 'warning';
            }
            // todo: .success for all ok, .warning for mixed, .danger for all failures
            $scope.messages.success = {type: 'add', alertType: alertType};
            $scope.dtInstance.reloadData();
        };
        $scope.updateProgressBar = function(text) {
            /* Updates progress bar message with either `text` for a specific
             message or the progress of the add phase of the addPeopleToCourse
             flow if `text` is missing.
             */
            // todo: this could/should be generic? ie default not add phase
            if (text) {
                $scope.messages.progress = text;
                return;
            }
            var completed = $scope.tracking.successes + $scope.tracking.failures ;
            if (completed < $scope.tracking.total) {
                $scope.messages.progress = 'Adding ' + (completed + 1)
                    + ' of ' + $scope.tracking.total;
            } else {
                $scope.messages.progress = 'Finishing...';
            }
        };
        $scope.warningsToDisplay = function() {
            return !$scope.operationInProgress && $scope.messages.warnings.length > 0;
        };

        // now actually init the controller
        $scope.clearMessages();  // initialize user-facing messages
        $scope.confirmRemoveModalInstance = null;
        $scope.courseInstanceId = $routeParams.courseInstanceId;

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
        $scope.operationInProgress = false;
        $scope.searchTerms = '';
        $scope.selectedRole = $scope.roles[0];
        $scope.setCourseInstance($routeParams.courseInstanceId);

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
