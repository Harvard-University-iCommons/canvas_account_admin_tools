(function() {
    var app = angular.module('CourseInfo');
    app.controller('PeopleController', PeopleController);

    function PeopleController($scope, angularDRF, $compile, courseInstances,
                              djangoUrl, $http, $log, $q, $routeParams,
                              $uibModal, $window, $filter) {
        // set up constants
        $scope.sortKeyByColumnId = {
            0: 'name',
            1: 'user_id',
            2: 'role__role_name',
            3: 'source_manual_registrar',
        };

        // Dictionary that contains information on all users in the table using their 'user_id as the key'
        $scope.peopleData = {};

        // Tracks the divID of any currently displayed popovers
        $scope.popOverID = null;

        // set up functions we'll be calling later
        $scope.addNewMember = function(personResult) {
            /* Make a call to add the person to the course as a new member
             if the person is:
             - successfully returned by a person lookup (lookupPeople)
             - not already enrolled in the course (unless dual-enrollment is allowed)
             - not represented by more than one profile
             Returns a promise representing the call made to add the new member
             to the course, or returns null if one or more of the above criteria fail
             */
            var memberRecords = personResult[0];
            var searchTerm = personResult[1];
            var peopleData = personResult[2];
            if (peopleData.length === 0) {
                // didn't find any people for the search term
                $scope.messages.warnings.push({
                    type: 'notFound',
                    searchTerm: searchTerm
                });
                $scope.tracking.failures++;
                return null
            }

            if (peopleData.length > 1) {
                $scope.messages.warnings.push({
                    type: 'multipleProfiles',
                    searchTerm: searchTerm,
                    // just pick the first one to find the name
                    name: $scope.getProfileFullName(peopleData[0]),
                    profiles: peopleData
                });
                $scope.tracking.failures++;
                return null
            }

            if (memberRecords.length === 0 || $scope.allowDualEnrollment(memberRecords, $scope.selectedRole.roleId)) {
                var name = $scope.getProfileFullName(peopleData[0]);
                var postParams = {
                    user_id: peopleData[0].univ_id,
                    role_id: $scope.selectedRole.roleId};
                return $scope.addNewMemberToCourse(postParams, name,
                        searchTerm)

            } else {
                // the user already has an enrollment in the course
                $scope.messages.warnings.push({
                    type: 'alreadyInCourse',
                    name: $scope.getProfileFullName(
                        peopleData[0]),
                    memberships: memberRecords,
                    searchTerm: searchTerm
                });
                $scope.tracking.failures++;
                return null
            }
        }

        $scope.getSchool = function() {
            return $scope.courseInstance.school.toLowerCase();
        }

        $scope.allowDualEnrollment = function(member, roleId) {
            // Allow a given member to be enrolled twice if:
            // - course is in GSD sub-account AND
            // - result is Guest/TA or Student/TA dual-enrollment

            var eligibleSchool = 'gsd';
            var maxAllowedRoles = 2;
            var memberRoleId = member[0].role.role_id;
            var allowedMapping = {
                0: [5],
                10: [5],
                5: [0, 10]
            };
            var allowedRoles = allowedMapping[roleId] ?? null;
            return (
                $scope.getSchool() === eligibleSchool
                && member.length < maxAllowedRoles
                && allowedRoles !== null
                && allowedRoles.indexOf(memberRoleId) !== -1
            );
        }

        $scope.addNewMemberToCourse = function(userPostParams, userName,
                                               searchTerm) {
            /* Adds a single person to the course; handles the actual posting of
             member info to the course via the API. Returns a promise for the
             POST call response.
             */
            var handlePostSuccess = function(response) {
                $scope.tracking.successes++;
                return response;
            };

            var handlePostError = function(response) {
                $scope.handleAjaxErrorResponse(response);
                var errorMessage = (((response||{}).data||{}).detail||'');
                if (errorMessage.indexOf('Canvas API error details') != -1) {
                    // There was a partial error (we caught
                    // a Canvas API error). The user has been added to the
                    // coursemanager db, but could not be added to Canvas.
                    // In this case it's possible that the user will be added
                    // during the next Canvas sync. We let the user know about
                    // the partial failure and that it may correct itself.
                    var concludedMessage = 'Can\'t add an enrollment to a concluded course';
                    if (errorMessage.indexOf(concludedMessage) != -1) {
                        $scope.tracking.concludedCourseSuccesses++;
                    } else {
                        $scope.messages.warnings.push({
                            type: 'partialFailure',
                            failureDetail: errorMessage,
                            name: userName,
                            searchTerm: searchTerm
                        });
                        $scope.tracking.failures++;
                    }
                }
                else {
                    $scope.messages.warnings.push({
                        type: 'addFailed',
                        name: userName,
                        searchTerm: searchTerm
                    });
                    $scope.tracking.failures++;
                }
                return response;
            };

            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                        ['api/course/v2/course_instances/'
                                         + $scope.courseInstanceId + '/people/']);

            return $http.post(url, userPostParams)
                .then(handlePostSuccess, handlePostError)
                .finally($scope.updateProgressBar)
        };

        $scope.addPeopleToCourse = function(searchTermList) {

            /* looks up HUIDs, XIDs, and/or email addresses from searchTerms
             and attempts to add people to the course who do not already have an
             enrollment.
             */

            $scope.clearMessages();
            $scope.operationInProgress = true;
            $scope.tracking.total = searchTermList.length;
            $scope.updateProgressBar('Looking up ' + $scope.tracking.total
                + ' people');
            var peoplePromises = $scope.lookupPeople(searchTermList);
            var addNewMemberPromises = [];
            peoplePromises.forEach(function setupAddPersonPromiseChain(personPromise) {
                addNewMemberPromises.push(
                    $q.all([personPromise])
                        .then((results) => {
                            var courseMemberPromises = results.map(person => $scope.lookupCourseMember(person));
                            return $q.all(courseMemberPromises);
                        })
                        .then((results) => {
                            var addNewMemberPromises = results.map(member => $scope.addNewMember(member));
                            return addNewMemberPromises;
                        }, (error) => {
                            // swallow rejected person lookup to allow others
                            // to proceed
                            return null;
                        }).finally($scope.updateProgressBar)
                    );
            });
            $q.all(addNewMemberPromises)
            .finally($scope.showAddNewMemberResults);;
        };

        $scope.clearMessages = function() {
            $scope.messages = {progress: null, success: null, warnings: []};
            $scope.tracking = {
                concludedCourseSuccesses: 0,
                failures: 0,
                successes: 0,
                total: 0,
                totalFailures: 0,
                totalSuccesses: 0
            };
            $scope.removeFailure = null;
            $scope.concludeDateUpdateMessage = {success: null, failure: null};
        };

        $scope.closeAlert = function(source) {
            $scope.messages[source] = null;
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

        $scope.confirmAddPeopleToCourse = function(searchTerms) {
            var searchTermList = $scope.getSearchTermList(searchTerms);
            // open a modal confirmation box and as the user to verify they want
            // to add the number of users they entered.
            $scope.confirmAddModalInstance = $uibModal.open({
                animation: true,
                templateUrl: 'partials/add-people-to-course-confirmation.html',
                controller: function ($scope, $uibModalInstance, numPeople,
                                      selectedRoleName) {
                    $scope.numPeople = numPeople;
                    $scope.selectedRoleName = selectedRoleName;
                },
                resolve: {
                    numPeople: function () {
                        return searchTermList.length;
                    },
                    selectedRoleName: function () {
                        return $scope.selectedRole.roleName;
                    }
                }
            });

            $scope.confirmAddModalInstance.result.then(function modalConfirmed() {
                $scope.addPeopleToCourse(searchTermList);
            })
            .finally(function() {
                $scope.confirmAddModalInstance = null;
            });
        };

        $scope.confirmRemove = function(membership) {
            // creates a new remove user confirmation modal, and
            // stashes this membership object on the modal's child scope.

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
                .then(function modalConfirmed(membership) {
                    $scope.removeMembership(membership);
                })
                .finally(function() {
                    $scope.confirmRemoveModalInstance = null;
                });
        };

        $scope.disableAddToCourseButton = function(){
            return ($scope.operationInProgress || ($scope.searchTerms.length == 0));
        };

        // todo: move this into a service/app.js?
        $scope.getCourseDescription = function(course) {
            // If a course's title is [NULL], attempt to display the short title.
            // If the short title is also [NULL], display [School] 'Untitled Course' [Term Display]
            if(typeof course.title != "undefined" && course.title.trim().length > 0){
                return course.title;
            }
            else if(typeof course.short_title != "undefined" && course.short_title.trim().length > 0){
                return course.short_title;
            }
            return 'Untitled Course';
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
                courseInstance['section'] = ci.section ? ci.section : '';
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
                    site.site_id = site.external_id ? site.external_id : site.course_site_url;
                    if (site.site_id.indexOf('http') === 0) {
                        site.site_id = site.site_id.substr(site.site_id.lastIndexOf('/')+1);
                    }
                    siteIds.push(site.site_id);
                });
                courseInstance['sites'] = sites;  // needed for sites tab
                courseInstance['site_list']= siteIds.length>0 ? siteIds.join(', ') : 'N/A';
            }
            return courseInstance;
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

        $scope.handleAngularDRFError = function(error) {
            $log.error(error);
        };

        $scope.isUnivID = function(searchTerm) {
            var re = /^[A-Za-z0-9]{8}$/;
            return re.test(searchTerm);
        };

        $scope.lookupCourseMember = function(person) {
            /* Given an array containing person data obtained
            via a people lookup (lookupPeople) and the original
            searchTerm, returns a promise representing a call
            to identify the person's enrollment in the course
            */
            var personData = person[0]
            var searchTerm = person[1];
            if (personData.length === 0) {
                return null
            }
            var univId = personData[0].univ_id;
            var courseMemberUrl = djangoUrl.reverse(
                                      'icommons_rest_api_proxy',
                                      ['api/course/v2/course_instances/' +
                                       $scope.courseInstanceId +
                                       '/people/' + univId]);

            var promiseConfig = {
                drf: {pageSize: 100},
            };

            var promise = angularDRF.get(courseMemberUrl, promiseConfig).then(
                    function includeSearchTermWithCourseMemberResult(result) {
                        return [result, searchTerm, personData];
                    },
                    function courseMemberLookupFailure(error) {
                        $scope.tracking.failures++;
                        $scope.messages.warnings.push({
                            type: 'courseMemberLookupFailed',
                            searchTerm: searchTerm
                        });
                        return $q.reject(error);
                    }
            );

            return promise
        };

        $scope.lookupPeople = function(searchTermList) {
            /* generates a list of promises (http requests to the API) for the
              search terms provided in order to get the univ_id for each
              person the user wants to add
              */
            var peopleURL = djangoUrl.reverse('icommons_rest_api_proxy',
                                              ['api/course/v2/people/']);
            var peoplePromiseList = [];

            searchTermList.forEach(function setupPersonLookup(searchTerm) {
                var promiseConfig = {
                    drf: {pageSize: 100},
                    params: {},
                };
                if ($scope.isUnivID(searchTerm)) {
                    promiseConfig.params.univ_id = searchTerm;
                } else {
                    promiseConfig.params.email_address = searchTerm;
                }
                var promise = angularDRF.get(peopleURL, promiseConfig).then(
                        function includeSearchTermWithPersonResult(result) {
                            return [result, searchTerm];
                        },
                        function personLookupFailure(error) {
                            $scope.tracking.failures++;
                            $scope.messages.warnings.push({
                                type: 'personLookupFailed',
                                searchTerm: searchTerm
                            });
                            return $q.reject(error);
                        }
                );
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

        $scope.renderRemove = function(data, type, full, meta) {
            return '<div class="text-center">' +
                   '<a href="" ng-click="confirmRemove(dtInstance.DataTable.data()[' + meta.row + '])" ' +
                   'data-sisid="' + full.user_id + '"><i class="fa fa-trash-o"></i></a></div>';
        };

        $scope.renderSource = function(data, type, full, meta) {
            return /^.*feed$/.test(data) ? 'Registrar Added' : 'Manually Added';
        };

        $scope.renderConcludeDate = function(data, type, full, meta) {
            // Create a wrapper div element to allow for easier access of the table cell
            var concludeDateDiv = '<div id="'+full.user_id+'">';
            var concludeDate = '';

            // If there is a conclude date, format it to be MM/dd/yyyy and create an input field
            if (full.conclude_date){
                // If the date is not split up, it returns an 'Invalid Date' in Safari
                var d = full.conclude_date.split(/[^0-9]/);
                concludeDate = $filter('date')(new Date(d[0],d[1]-1,d[2],d[3],d[4],d[5] ), 'MM/dd/yyyy', 'Z');
            }
            concludeDateDiv += $scope.getCalButtonHTML(full.user_id, concludeDate);

            concludeDateDiv += '</div>';

            return concludeDateDiv;
        };

        $scope.getInputHTML= function(id, value) {
            var inputHTML = '<div class="input-group">' +
                                 '<input type="text" class="form-control" id="input-'+id+'" value="'+value+'"/>' +
                                 '<label class="input-group-addon btn" for="input-'+id+'">' +
                                    '<span class="fa fa-calendar"></span>' +
                                '</label>' +
                             '</div>';
            return inputHTML;
        };

        $scope.getCalButtonHTML= function(id, value) {
             var calHTML =  '<div class="col-sm-10">'+value+'</div>' +
                            '<div class="col-sm-2">' +
                               '<a href="" ng-click=createInputField("'+id+'","'+value+'"\)>' +
                                   '<span class="fa fa-calendar"></span>' +
                               '</a>' +
                           '</div>';

             return calHTML;
        };

        $('body').on('focus',".input-group", function(){
            if($scope.popOverID) {
                $('#'+$scope.popOverID).popover('destroy');
                $scope.popOverID = null;
            }


            // Get the user ID, which will be used in the PATCH and html transformation events
            var userID = $(this).parent().attr('id');
            var inputElement = $(this).find('input');
            var previousValue = inputElement.val();

            var dp = inputElement.datepicker({
                autoclose: true,
                todayHighlight: 1
            });

            // When the date picker window has been closed, validate the selected date and send PATCH
            dp.on('hide', function() {
                $scope.clearMessages();
                var selectedDate = inputElement.val();

                // Only begin the update call process if the selected date differs from the original value
                if (selectedDate != previousValue) {
                    // We only accept dates from tomorrow onward
                    if ($scope.isSelectedDateInPast(selectedDate)) {
                        // Set a .1 second delay before displaying error message.
                        // When the datepicker is closed, it creates a click event which would close this display
                        // before it is rendered.
                        setTimeout(
                            function() {
                              $scope.addPopOverToCell(userID, 'failure', 'You can only pick a date in the future.');
                            }, 100)
                    } else {
                        var roleID = $scope.peopleData[userID]['role']['role_id'];
                        $scope.updateConcludeDate(userID, roleID, selectedDate);
                    }
                }
                $scope.createCalButton(userID, selectedDate);
            });

        });


        $(document).on('click', function() {
            if($scope.popOverID) {
                $('#'+$scope.popOverID).popover('destroy');
                $scope.popOverID = null;
            }
        });


        // Adds a popover to the given divID with the styling of the given type (success/failure)
        // Popover will contain the given message
        $scope.addPopOverToCell = function(divID, type, message) {
            $scope.popOverID = divID;
            var  messageType = (type == 'success') ?  'success' : 'danger';
            var popOverTemplate = '<div class="popover popover-'+messageType+'" role="tooltip">' +
                                       '<div class="arrow"></div>' +
                                       '<h3 class="popover-title"></h3>' +
                                       '<div class="popover-content"></div>' +
                                   '</div>';

            var popOverSettings = {
                placement: 'top',
                content: message,
                delay: 100,
                template: popOverTemplate
            };

            // Create the popover and show it
            $('#'+divID).popover(popOverSettings).popover('show');
        };

        // Creates an input field in the given div ID
        $scope.createInputField = function(divID, inputVal) {
            inputVal = (typeof inputVal !== 'undefined') ? inputVal : '';
            var input_group = $scope.getInputHTML(divID, inputVal);

            $('#'+divID).html($compile(angular.element(input_group))($scope));

            if(inputVal == '') {
                // Focus on the new input field to generate the date picker
                $('#'+divID).find('input').focus();
            }
        };

        // Creates a calendar button for the given divID
        $scope.createCalButton = function(divID, concludeDate) {
            concludeDate = (typeof concludeDate !== 'undefined') ? concludeDate : '';
            var cal_button = $scope.getCalButtonHTML(divID, concludeDate);

            $('#'+divID).html($compile(angular.element(cal_button))($scope));
        };

        // Converts the mm/dd/yyyy date to a 12:01, ISO format
        $scope.formatConcludeDate = function(date) {
            var concludeDate = null;
            if (date) {
                date = date+ ' 00:01:00'
                concludeDate = new Date(date).toISOString();
            }
            return concludeDate;
        };

        // Checks if the given date is prior to tomorrow's date(today's date plus 1).
        $scope.isSelectedDateInPast = function(selectedDate) {
            // Since the input field is a string representation of a date,
            // we need to convert tomorrow's date to the same format as a string to make the comparison.
            var today = new Date();
            var tomorrow = new Date();
            tomorrow.setDate(today.getDate() + 1);
            var tmrwString = (tomorrow.getMonth() + 1) + '/' + tomorrow.getDate() + '/' +  tomorrow.getFullYear();
            return Date.parse(selectedDate)-Date.parse(tmrwString)<0;
        };

        // Perform the PATCH with the given user ID, role_id, conclude_date
        $scope.updateConcludeDate = function(userID, roleID, concludeDate) {
            var patchData = {
                'user_id': userID,
                'role_id': roleID,
                'conclude_date': $scope.formatConcludeDate(concludeDate)
            };
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                        ['api/course/v2/course_instances/'
                                         + $scope.courseInstanceId + '/people/' + userID + '/']);

            $http.patch(url, patchData)
                .success(function finalizeCourseDetailsPatch() {
                    // If update is successful, then touch the course instance so the last_updated field is updated
                    // so that changes will be picked up in feed
                    $scope.updateCourseInstanceLastUpdated();
                    // Reset the display to show conclude date and calendar button
                    $scope.createCalButton(patchData['user_id'], concludeDate);
                    $scope.addPopOverToCell(userID, 'success', 'The enrollment details have been updated.');
                })
                .error(function(data, status, headers, config, statusText) {
                    $scope.handleAjaxError(data, status, headers, config, statusText);
                    $scope.addPopOverToCell(userID, 'failure', 'An error occurred during the update.');
                })
        };

        // Updates the current course instances 'last_updated' field to be the current date and time.
        $scope.updateCourseInstanceLastUpdated = function() {
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                        ['api/course/v2/course_instances/'
                                         + $scope.courseInstanceId + '/']);
            $http.patch(url);
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
                            // if people/members are fetched first, we don't
                            // want to overwrite the members attribute of
                            // $scope.courseInstance
                            $.extend($scope.courseInstance,
                                $scope.getFormattedCourseInstance(data));
                        }else{
                            $log.error(' CourseInstance record mismatch for id :'
                                + id +',  fetched record for :' +data.id);
                        }
                    })
                    .error($scope.handleAjaxError);
            }
        };

        $scope.showAddNewMemberResults = function() {
            /* Updates page with summary message and failure details after all
             add person operations are finished.
             */
            // use 'totalX's to avoid stomping existing 'X's
            $scope.tracking.totalSuccesses = $scope.tracking.successes +
                                             $scope.tracking.concludedCourseSuccesses;
            $scope.tracking.totalFailures = $scope.tracking.total -
                                            $scope.tracking.totalSuccesses;
            // figure out the alert type (ie. the color) here
            var alertType = '';
            if ($scope.tracking.totalSuccesses == 0) {
                alertType = 'danger';
            }
            else if ($scope.tracking.totalFailures == 0) {
                alertType = 'success';
            }
            else {
                alertType = 'warning';
            }
            $scope.messages.success = {type: 'add', alertType: alertType};
            // only reload if we expect to see immediate changes to enrollment
            if ($scope.tracking.totalSuccesses) {
                $scope.dtInstance.reloadData();
            }
            $scope.operationInProgress = false;
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
            var completed = $scope.tracking.successes +
                            $scope.tracking.concludedCourseSuccesses +
                            $scope.tracking.failures ;
            if (completed < $scope.tracking.total) {
                $scope.messages.progress = 'Adding ' + (completed + 1)
                    + ' of ' + $scope.tracking.total;
            } else {
                $scope.messages.progress = 'Finishing...';
            }
        };
        $scope.warningsToDisplay = function() {
            return (!$scope.operationInProgress && ($scope.messages.warnings.length > 0));
        };

        // now actually init the controller
        $scope.clearMessages();  // initialize user-facing messages
        $scope.confirmRemoveModalInstance = null;
        $scope.courseInstanceId = $routeParams.courseInstanceId;
        $scope.courseInstance = {};
        $scope.initialCourseMembersFetched = false;  // UI component visibility

        $scope.roles = [];
        Array.prototype.push.apply($scope.roles, $window.roles);
        $scope.operationInProgress = false;
        $scope.searchTerms = '';

        $scope.selectedRole = $scope.roles.filter(function(role){
            return role['roleName']=="Guest";
        })[0];

        $scope.setCourseInstance($routeParams.courseInstanceId);

        // configure the alert datatable
        $scope.dtOptionsWarning = {
            searching: false,
            paging: false,
            ordering: ([1, 'asc']),
            info : false
        };

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
                    dataType: 'json'
                }).done(function dataTableGetDone(data, textStatus, jqXHR) {
                    $scope.courseInstance.members = data.count;
                    callback({
                        recordsTotal: data.count,
                        recordsFiltered: data.count,
                        data: data.results,
                    });
                })
                .fail(function dataTableGetFail(data, textStatus, errorThrown) {
                    $log.error('Error getting data from ' + url + ': '
                               + textStatus + ', ' + errorThrown);
                    callback({
                        recordsTotal: 0,
                        recordsFiltered: 0,
                        data: [],
                    });
                })
                .always(function dataTableGetAlways() {
                    // notify UI to stop showing a loading... message
                    $scope.initialCourseMembersFetched = true;
                    $scope.$digest();
                });
            },
            createdRow: function( row, data, dataIndex ) {
                // Build a dict of the retrieved users, with the user_id as the key and their data as the values
                $scope.peopleData[data['user_id']] = data;

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
                processing: 'Loading, please wait...'
            },
            lengthMenu: [10, 25, 50, 100],
            processing: true,
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
            {
                data: 'role.role_name',
                title: 'Role'
            },
            {
                data: 'source',
                render: $scope.renderSource,
                title: 'Source',
            },
            {
                data: 'source',
                render: $scope.renderConcludeDate,
                title: 'Conclusion Date Override',
                orderable: false,
            },
            {
                data: '',
                orderable: false,
                render: $scope.renderRemove,
                title: 'Remove',
            }
        ];
    }
})();
