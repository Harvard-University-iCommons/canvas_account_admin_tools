(function () {
    angular.module('CourseInfo')
        .controller('SitesController', SitesController);

    // todo: remove unused providers
    function SitesController($scope, courseInstances, $compile, djangoUrl,
                               $http, $location, $log, $q, $routeParams, $sce,
                               $uibModal, view) {

        var sc = this;
        // there are two kinds of alerts, global (which appear at the top of the
        // page/form) and form-level (which appear next to a form label, inside
        // the form, giving a field-level context to the message)
        sc.alerts = {form: {}, global: {}};
        sc.apiBase = 'api/course/v2/course_instances/';
        sc.apiProxy = 'icommons_rest_api_proxy';
        sc.associateNewSiteInProgress = false;
        sc.courseSitesUpdateInProgress = false;
        sc.courseInstanceId = $routeParams.courseInstanceId;
        sc.courseInstance = {};
        sc.courseInstances = courseInstances;
        sc.dissociateSiteInProgressIndex = null;
        sc.editable = false;
        sc.newCourseSiteURL = '';
        sc.tabIndexesByView = {'details': 0, 'people': 1, 'sites': 2};
        // `view` comes from route resolve() function
        sc.activeTabIndex = sc.tabIndexesByView[view];

        sc.init = function() {
            var instances = courseInstances.instances;
            if (instances && instances[sc.courseInstanceId]) {
                sc.courseInstance = sc.getFormattedCourseInstance(
                    instances[sc.courseInstanceId]);
            }
            sc.fetchCourseInstanceDetails(sc.courseInstanceId);
        };

        sc.alertPresent = function(alertType, alertKey) {
            return (sc.alerts[alertType][alertKey] &&
                    sc.alerts[alertType][alertKey].show);
        };

        sc.associateNewSite = function() {
            sc.associateNewSiteInProgress = true;
            data = {
              'external_id': sc.newCourseSiteURL
            };
            var post_course_site_url = djangoUrl.reverse(sc.apiProxy,
                        [sc.apiBase + sc.courseInstance.course_instance_id + '/sites/']);
            $http.post(post_course_site_url, data).then(function(response){
                var new_course = {
                    course_site_url: sc.newCourseSiteURL,
                    map_type: 'official',
                    site_map_id: response.data.site_map_id
                };
                sc.courseInstance.sites.push(new_course);
                sc.newCourseSiteURL = '';
            }, function(response) {
                sc.handleAjaxErrorResponse(response);
                sc.alerts.form.siteOperationFailed = {
                    show: true,
                    operation: 'associating',
                    details: response.statusText || 'None'};
                }
            ).finally(function(){
                sc.associateNewSiteInProgress = false;
            });
        };

        sc.associateNewSiteHandleKey = function(keypressEvent) {
            // if user hits Enter in the new site URL form input field, capture
            // it for handling by associateNewSite() and prevent it from
            // triggering main form submission
            if (keypressEvent.keyCode == 13) {
                // swallow the enter key no matter what; this prevents a blank
                // input causing the main form to be submitted
                keypressEvent.preventDefault();
                if (sc.validNewSiteURL()) {
                    sc.associateNewSite();
                }
            }
        };

        sc.dissociateSite = function(siteListIndex) {
            sc.confirmDissociateSiteModalInstance = $uibModal.open({
                animation: true,
                templateUrl: 'partials/dissociate-site-confirmation.html',
                controller: function ($scope, $uibModalInstance, siteURL, site_map_id) {
                    sc.siteURL = siteURL;
                    sc.site_map_id = site_map_id;
                },
                resolve: {
                    siteURL: function () {
                        return sc.courseInstance.sites[siteListIndex].course_site_url;
                    },
                    site_map_id: function() {
                        return sc.courseInstance.sites[siteListIndex].site_map_id;
                    }
                }
            });
            sc.confirmDissociateSiteModalInstance.result.then(
                function modalConfirmed() {
                    var delete_course_site_url = djangoUrl.reverse(sc.apiProxy,
                        [sc.apiBase + sc.courseInstance.course_instance_id + '/sites/' + sc.courseInstance.sites[siteListIndex].site_map_id + '/']);
                    $http.delete(delete_course_site_url)
                        .then(function(response){
                            sc.dissociateSiteInProgressIndex = siteListIndex;
                            sc.courseInstance.sites.splice(siteListIndex, 1);
                        }, function(response){
                            sc.handleAjaxErrorResponse(response);
                            sc.alerts.form.siteOperationFailed = {
                                show: true,
                                operation: 'dissociating',
                                details: response.statusText || 'None'};
                        }).finally(function(){
                            sc.dissociateSiteInProgressIndex = null;
                        });
            });
        };

        // todo: this should be a service that can be reused 
        sc.fetchCourseInstanceDetails = function (id) {

            var course_url = djangoUrl.reverse(sc.apiProxy,
                [sc.apiBase + id + '/']);

            var members_url = djangoUrl.reverse(sc.apiProxy,
                [sc.apiBase + id + '/people/']);

            var membersQueryConfig = {
                params: { '-source': 'xreg_map' }  // exclude xreg people
            };

            $http.get(course_url)
                .then(sc.handleCourseInstanceResponse,
                    function cleanUpFailedCourseDetailsGet(response) {
                        sc.handleAjaxErrorResponse(response);
                        sc.showNewGlobalAlert('fetchCourseInstanceFailed',
                            response.statusText);
                });

            $http.get(members_url, membersQueryConfig)
                .then(sc.handlePeopleResponse,
                    function cleanUpFailedCourseMembersGet(response) {
                        sc.handleAjaxErrorResponse(response);
                        // field-level error, do not reset global alerts
                        sc.alerts.form.fetchMembersFailed = {
                            show: true,
                            details: response.statusText || 'None'};
                });

        };
        // todo: move this into a service/app.js?
        sc.getCourseDescription = function(course) {
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
        sc.getFormattedCourseInstance = function (ciData) {
            // This is a helper function that formats the raw CourseInstance
            // API response data for display in the UI
            var ci = ciData;  // shorten for brevity, preferable to `with()`
            var courseInstance = {};
            if (ci) {
                courseInstance['title'] = ci.title;
                courseInstance['school'] = ci.course.school_id.toUpperCase();
                courseInstance['term'] = ci.term.display_name;
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
                courseInstance['conclude_date'] = ci.conclude_date;
                courseInstance['sync_to_canvas'] = ci.sync_to_canvas;
                courseInstance['exclude_from_isites'] = ci.exclude_from_isites;
                courseInstance['exclude_from_catalog'] = ci.exclude_from_catalog;

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

        sc.getPeopleTabHeading = function() {
            var memberCount = (sc.courseInstance || {}).members;
            switch (memberCount) {
                case undefined:
                    return 'People';
                case 1:
                    return '1 Person';
                default:
                    return memberCount + ' People';
            }
        };

        // todo: refactor/collapse, and put in tab controller
        sc.getSitesTabHeading = function() {
            var siteList = (sc.courseInstance || {}).sites;
            if (!angular.isArray(siteList)) { return 'Associated Sites' }
            if (siteList.length == 1) {
                return '1 Associated Site';
            } else {
                return siteList.length + ' Associated Sites';
            }
        };

        sc.handleAjaxErrorResponse = function(r) {
            sc.handleAjaxError(
                r.data, r.status, r.headers, r.config, r.statusText);
        };

        sc.handleAjaxError = function (data, status, headers, config, statusText) {
            $log.error('Error attempting to ' + config.method + ' ' + config.url +
                ': ' + status + ' ' + statusText + ': ' + JSON.stringify(data));
        };

        sc.handleCourseInstanceResponse = function(response) {
            //check if the right data was obtained before storing it
            if (response.data.course_instance_id == sc.courseInstanceId) {
                courseInstances.instances[response.data.course_instance_id] = response.data;
                // if people/members are fetched first, we don't want to
                // overwrite the members attribute of sc.courseInstance
                $.extend(sc.courseInstance,
                    sc.getFormattedCourseInstance(response.data));
                // TLT-2376: only sandbox and ILE courses are currently editable
                var rc = response.data.course.registrar_code;
                sc.editable = sc.isCourseInstanceEditable(rc);
            } else {
                $log.error('CourseInstance record mismatch for id :'
                    + sc.courseInstanceId + ', instead received record for '
                    + response.data.id);
            }
        };

        sc.handlePeopleResponse = function(response) {
            sc.courseInstance['members'] = response.data.count;
        };

        sc.isCourseInstanceEditable = function(courseRegistrarCode) {
            // TLT-2376: sandbox and ILE courses are editable, and are
            // identified by their course (registrar) code
            return (courseRegistrarCode.startsWith('ILE-') ||
                    courseRegistrarCode.startsWith('SB-'));
        };

        sc.isUndefined = function(obj) {
            // calling angular.isUndefined() directly from the directive
            // does not seem to work; wrapping it in a function that is watched
            // on the controller scope works as expected
            return angular.isUndefined(obj);
        };

        sc.resetGlobalAlerts = function() {
            sc.alerts.global = {};  // reset any existing global alerts
        };

        sc.scrollToTopOfViewport = function() {
            scrollTo(0, 0);  // scroll to top of form
        };

        sc.showNewGlobalAlert = function(alertKey, alertDetail) {
            // reset any global alerts currently showing, reposition viewport at
            // top of iframe so we can see notification messages, and show new
            // alert, where param alertKey is the name/type of global alert and
            // alertDetail is an optional way to provide more details to the
            // user in the alert message box
            sc.resetGlobalAlerts();
            sc.scrollToTopOfViewport();
            sc.alerts.global[alertKey] = {
                show: true,
                details: alertDetail || 'None'};

        };

        // todo: make this part of a service/app so it's reusable
        sc.switchToRoute = function(routeName, courseId) {
            if (['details', 'people', 'sites'].indexOf(routeName) > -1) { 
                $location.path('/' + routeName + '/' + courseId);
            } else {
                // default to search view
                $location.path('/');
            }
        };

        sc.validNewSiteURL = function() {
            // if we use the required or ngRequired directives on our new site
            // URL input element then the main form will also recognize and
            // require them; instead we need to use a combination of empty input
            // checking and the angular input directive's built-in validation.
            return (sc.newCourseSiteURL.trim() != '' &&
                    sc.courseSitesForm.newAssociatedCourseURL.$valid);
        };

        sc.init();
    }
})();
