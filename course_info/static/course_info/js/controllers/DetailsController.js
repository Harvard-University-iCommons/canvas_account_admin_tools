(function () {
    angular.module('CourseInfo')
        .controller('DetailsController', DetailsController);


    function DetailsController(courseInstances, djangoUrl, $http, $log,
                               $routeParams, $filter, $scope) {

        var dc = this;
        // there are two kinds of alerts, global (which appear at the top of the
        // page/form) and form-level (which appear next to a form label, inside
        // the form, giving a field-level context to the message)
        dc.alerts = {form: {}, global: {}};
        dc.apiBase = 'api/course/v2/course_instances/';
        dc.apiProxy = 'icommons_rest_api_proxy';
        // $routeParams['fromsearchpeople'] expects a `univ_id` to build a link
        // to the search people app's course list route
        // todo: there may be a more generic, extensible approach
        dc.arrivedFromPeopleCourses = $routeParams['frompeoplecourses'];
        dc.courseDetailsUpdateInProgress = false;
        dc.courseInstanceId = $routeParams.courseInstanceId;
        dc.courseInstance = {};
        dc.courseInstances = courseInstances;
        // if a course is `editable` then user can update fields other than
        // course flags; all courses can be edited, but this `editable` value
        // controls how many fields are available to edit
        dc.editable = false;
        dc.editInProgress = false;  // has edit mode been activated by user

        // Sets the show boolean value of the date picker form alert.
        dc.toggleDatePickerAlert = function(val) {
            dc.alerts.form['invalidDatePicked'] = {
                show: val
            };
            $scope.$digest();
        };

        dc.init = function() {
            var instances = courseInstances.instances;
            if (instances && instances[dc.courseInstanceId]) {
                dc.courseInstance = dc.getFormattedCourseInstance(instances[dc.courseInstanceId]);
            }
            dc.fetchCourseInstanceDetails(dc.courseInstanceId);
        };

        dc.alertPresent = function(alertType, alertKey) {
            return (dc.alerts[alertType][alertKey] &&
                    dc.alerts[alertType][alertKey].show);
        };

        dc.fetchCourseInstanceDetails = function (id) {

            var course_url = djangoUrl.reverse(dc.apiProxy,
                [dc.apiBase + id + '/']);

            var members_url = djangoUrl.reverse(dc.apiProxy,
                [dc.apiBase + id + '/people/']);

            var membersQueryConfig = {
                params: { '-source': 'xreg_map' }  // exclude xreg people
            };

            $http.get(course_url)
                .then(dc.handleCourseInstanceResponse,
                    function cleanUpFailedCourseDetailsGet(response) {
                        dc.handleAjaxErrorResponse(response);
                        dc.showNewGlobalAlert('fetchCourseInstanceFailed',
                            response.statusText);
                });

            $http.get(members_url, membersQueryConfig)
                .then(dc.handlePeopleResponse,
                    function cleanUpFailedCourseMembersGet(response) {
                        dc.handleAjaxErrorResponse(response);
                        // field-level error, do not reset global alerts
                        dc.alerts.form.fetchMembersFailed = {
                            show: true,
                            details: response.statusText || 'None'};
                });
        };
        // todo: move this into a service/app.js?
        dc.getCourseDescription = function(course) {
            // If a course's title is [NULL], attempt to display the short title
            // If the short title is also [NULL], display 'Untitled Course'
            if(typeof course.title != "undefined" && course.title.trim().length > 0){
                return course.title;
            }
            else if(typeof course.short_title != "undefined" && course.short_title.trim().length > 0){
                return course.short_title;
            }
            return 'Untitled Course';
        };
        dc.getFormattedCourseInstance = function (ciData) {
            // This is a helper function that formats the raw CourseInstance
            // API response data for display in the UI
            var ci = ciData;  // shorten for brevity, preferable to `with()`
            var courseInstance = {};
            if (ci) {
                courseInstance['title'] = ci.title;
                courseInstance['school'] = ci.course.school_id.toUpperCase();
                courseInstance['term'] = ci.term.display_name;
                courseInstance['term_id'] = ci.term.term_id.toString();
                courseInstance['term_conclude_date'] = $filter('date')(ci.term.conclude_date, 'MM/dd/yyyy', 'Z');
                courseInstance['year'] = ci.term.academic_year;
                courseInstance['departments'] = ci.course.departments;
                courseInstance['course_groups'] = ci.course.course_groups;

                var registrarCode = ci.course.registrar_code_display
                    ? ci.course.registrar_code_display
                    : ci.course.registrar_code;

                courseInstance['registrar_code_display'] = registrarCode.trim();

                courseInstance['description'] = ci.description;
                courseInstance['short_title'] = ci.short_title;
                courseInstance['sub_title'] = ci.sub_title;
                courseInstance['meeting_time'] = ci.meeting_time;
                courseInstance['location'] = ci.location;
                courseInstance['instructors_display'] = ci.instructors_display;
                courseInstance['course_instance_id'] = ci.course_instance_id;
                courseInstance['notes'] = ci.notes;
                courseInstance['conclude_date'] = $filter('date')(ci.conclude_date, 'MM/dd/yyyy', 'Z');
                courseInstance['sync_to_canvas'] = ci.sync_to_canvas;
                courseInstance['exclude_from_isites'] = ci.exclude_from_isites;
                courseInstance['section'] = ci.section ? ci.section : '';

                if (ci.secondary_xlist_instances &&
                    ci.secondary_xlist_instances.length > 0) {
                    courseInstance['xlist_status'] = 'Primary';
                } else if (ci.primary_xlist_instances &&
                    ci.primary_xlist_instances.length > 0) {
                    courseInstance['xlist_status'] = 'Secondary';
                } else {
                    courseInstance['xlist_status'] = 'N/A';
                }

                courseInstance['sites'] = ci.sites;
            }

            return courseInstance;
        };

        dc.getTermList = function() {
            var termUrl = djangoUrl.reverse(dc.apiProxy, ['api/course/v2/terms/']);
            var now = new Date();
            var previousYear = now.getFullYear()-1;

            var termQueryConfig = {
                params: {
                    'calendar_year__gte': previousYear,
                    'school': dc.courseInstance['school'].toLowerCase(),
                    'limit': 100,
                    'ordering': '-end_date'
                }
            };

            var ongoingTermQueryConfig = {
                params: {
                    'academic_year': '1900',
                    'school': dc.courseInstance['school'].toLowerCase()
                }
            };

            $http.get(termUrl, termQueryConfig)
                .then(function successCallback(response) {
                    dc.termList = response.data.results;
                    $http.get(termUrl, ongoingTermQueryConfig)
                        .then(function successCallback(response) {
                            // Append the Ongoing term to the term list as it was filtered out of the initial get
                            dc.termList.push(response.data.results[0]);
                            // If the course is in a term older than 1 calendar year from today,
                            // append the term to the term list
                            dc.verifyTermList();
                        });
                }, function errorCallback(response) {
                    console.log(response.statusText);
                });

            dc.editable = true;
        };

        dc.verifyTermList = function() {
            // Checks to see if the course's term is in the filtered list of terms.
            // If it is not, then append it to the controllers term list
            var termInList = false;
            dc.termList.forEach(function(term) {
                if (term['term_id'] == dc.courseInstance['term_id']) {
                    termInList = true;
                }
            });
            if (!termInList) {
                dc.termList.unshift(
                    {
                        'display_name': dc.courseInstance.term,
                        'term_id': dc.courseInstance.term_id
                    }
                );
            }
        };

        dc.getPeopleCoursesRoute = function() {
            // returns URL for the Search People app's course list
            // route for the user specified by dc.arrivedFromPeopleCourses
            return window.globals.append_resource_link_id('../people_tool/')
                + '#/people/' + dc.arrivedFromPeopleCourses + '/courses/';
        };
        dc.handleAjaxErrorResponse = function(r) {
            dc.handleAjaxError(
                r.data, r.status, r.headers, r.config, r.statusText);
        };

        dc.handleAjaxError = function (data, status, headers, config, statusText) {
            $log.error('Error attempting to ' + config.method + ' ' + config.url +
                ': ' + status + ' ' + statusText + ': ' + JSON.stringify(data));
        };

        dc.handleCourseInstanceResponse = function(response) {
            //check if the right data was obtained before storing it
            if (response.data.course_instance_id == dc.courseInstanceId) {
                courseInstances.instances[response.data.course_instance_id] = response.data;
                // if people/members are fetched first, we don't want to
                // overwrite the members attribute of dc.courseInstance
                $.extend(dc.courseInstance,
                    dc.getFormattedCourseInstance(response.data));
                // TLT-2376: only sandbox and ILE courses are currently editable
                var rc = response.data.course.registrar_code;
                // Only get the term list if this course is editable
                if (dc.isCourseInstanceEditable(rc)) {
                    // Once the CI has been loaded, proceed to get the term list
                    dc.getTermList();
                }
                dc.resetForm();
            } else {
                $log.error('CourseInstance record mismatch for id :'
                    + dc.courseInstanceId + ', instead received record for '
                    + response.data.id);
            }
        };

        dc.handlePeopleResponse = function(response) {
            dc.courseInstance['members'] = response.data.count;
        };

        dc.isCourseInstanceEditable = function(courseRegistrarCode) {
            // TLT-2376: sandbox and ILE courses are editable, and are
            // identified by their course (registrar) code
            return (courseRegistrarCode.startsWith('ILE-') ||
                    courseRegistrarCode.startsWith('SB-'));
        };

        dc.isUndefined = function(obj) {
            // calling angular.isUndefined() directly from the directive
            // does not seem to work; wrapping it in a function that is watched
            // on the controller scope works as expected
            return angular.isUndefined(obj);
        };

        dc.resetForm = function() {
            dc.formDisplayData = angular.copy(dc.courseInstance);
            dc.resetFormAlerts();
            dc.editInProgress = false;
        };

        dc.resetFormFromUI = function() {
            dc.resetForm();
            dc.showNewGlobalAlert('formReset');
        };

        dc.resetFormAlerts = function () {
            dc.alerts.form = {};
        };

        dc.resetGlobalAlerts = function() {
            dc.alerts.global = {};  // reset any existing global alerts
        };

        dc.scrollToTopOfViewport = function() {
            scrollTo(0, 0);  // scroll to top of form
        };

        dc.showNewGlobalAlert = function(alertKey, alertDetail) {
            // reset any global alerts currently showing, reposition viewport at
            // top of iframe so we can see notification messages, and show new
            // alert, where param alertKey is the name/type of global alert and
            // alertDetail is an optional way to provide more details to the
            // user in the alert message box
            dc.resetGlobalAlerts();
            dc.scrollToTopOfViewport();
            dc.alerts.global[alertKey] = {
                show: true,
                details: alertDetail || 'None'};

        };

        dc.submitCourseDetailsForm = function() {
            // disables form, buttons
            dc.courseDetailsUpdateInProgress = true;
            var patchData = {};
            var url = djangoUrl.reverse(dc.apiProxy,
                [dc.apiBase + dc.courseInstanceId + '/']);
            // we could also get these from editable properties on the DOM
            var fields = [
                'description',
                'instructors_display',
                'location',
                'meeting_time',
                'notes',
                'short_title',
                'sub_title',
                'title',
                'sync_to_canvas',
                'exclude_from_isites',
                'section',
                'conclude_date',
                'term'
            ];
            fields.forEach(function(field) {
                if (field == 'conclude_date') {
                    // Conclude date is a DateTimeField in the CI model.
                    // Convert the formatted date back into a DateTime string to be submitted.
                    if (dc.formDisplayData['conclude_date']) {
                        // Validate that the selected date is not in the past before submitting.
                        if (!dc.isSelectedDateInPast(dc.formDisplayData['conclude_date'])) {
                            var formatted_date = new Date(dc.formDisplayData['conclude_date']+' 00:01:00').toISOString();
                            patchData['conclude_date'] = formatted_date;
                        }
                    } else {
                        // If the conclude date field is left blank, then set the conclude_date to null in the DB.
                        patchData['conclude_date'] = null;
                    }
                } else if (field == 'term') {
                    patchData['term'] = dc.formDisplayData['term_id'];
                } else {
                    patchData[field] = dc.formDisplayData[field];
                }
            });

            $http.patch(url, patchData)
                .then(function finalizeCourseDetailsPatch(response) {
                    // update form data so reset button will pick up changes
                    angular.extend(dc.courseInstance, dc.getFormattedCourseInstance(response.data));
                    dc.showNewGlobalAlert('updateSucceeded');
                }, function cleanUpFailedCourseDetailsPatch(response) {
                    dc.handleAjaxErrorResponse(response);
                    dc.showNewGlobalAlert('updateFailed', errorMessage);
                })
                .finally( function courseDetailsUpdateNoLongerInProgress() {
                    // leaves 'edit' mode, re-enables edit button
                    dc.courseDetailsUpdateInProgress = false;
                    if (dc.formDisplayData['conclude_date']) {
                        // Only update the display conclude date if a valid date was entered.
                        if (!dc.isSelectedDateInPast(dc.formDisplayData['conclude_date'])) {
                            // Reformat the conclude date
                            dc.courseInstance['conclude_date'] = $filter('date')(new Date(dc.formDisplayData['conclude_date']), 'MM/dd/yyyy', 'Z');
                        }
                    }
                    dc.resetForm();
                });
        };

        dc.toggleEditMode = function() {
            dc.editInProgress = !dc.editInProgress;
            dc.resetGlobalAlerts();
        };

        dc.init();

        // Checks if the given date is prior to tomorrow's date(today's date plus 1).
        dc.isSelectedDateInPast = function(selectedDate) {
            // Since the input field is a string representation of a date,
            // we need to convert tomorrow's's date to the same format as a string to make the comparison.
            var today = new Date();
            var tomorrow = new Date();
            tomorrow.setDate(today.getDate() + 1);
            var tmrwString = (tomorrow.getMonth() + 1) + '/' + tomorrow.getDate() + '/' +  tomorrow.getFullYear();
            return Date.parse(selectedDate)-Date.parse(tmrwString)<0;
        }
    }
})();
