// TODO - this is pretty much a copy of the people controller with some mods.
// TODO - this still needs a lot of clean up, we don't need everything in here

(function () {
    var app = angular.module('CourseInfo');
    app.controller('DetailsController', DetailsController);

    function DetailsController($scope, $routeParams, courseInstances, $compile,
                               djangoUrl, $http, $q, $log, $uibModal, $sce) {

        dc = this;

        dc.handleAjaxError = function (data, status, headers, config, statusText) {
            $log.error('Error attempting to ' + config.method + ' ' + config.url +
                ': ' + status + ' ' + statusText + ': ' + JSON.stringify(data));
        };

        dc.handleLookupResults = function(results) {
            var courseResult = results[0];
            var membersResult = results[1];

            //check if the right data was obtained before storing it
            if (courseResult.data.course_instance_id == dc.courseInstanceId) {
                courseInstances.instances[courseResult.data.course_instance_id] = courseResult.data;
                dc.courseInstance = dc.getFormattedCourseInstance(courseResult.data, membersResult.data)
            } else {
                $log.error(' CourseInstance record mismatch for id :'
                    + dc.courseInstanceId + ',  fetched record for :' + courseResult.data.id);
            }
        };

        dc.setCourseInstance = function (id) {

            var course_url = djangoUrl.reverse(
                'icommons_rest_api_proxy',
                ['api/course/v2/course_instances/' + id + '/']);

            var members_url = djangoUrl.reverse(
                'icommons_rest_api_proxy',
                ['api/course/v2/course_instances/'
                + id + '/people/']);

            var coursePromise = $http.get(course_url)
                .error(dc.handleAjaxError);

            var membersPromise = $http.get(members_url)
                .error(dc.handleAjaxError);

            $q.all([coursePromise, membersPromise])
                .then(dc.handleLookupResults);
        };

        dc.stripQuotes = function(str){
            return str ? str.trim().replace(new RegExp("^\"|\"$", "g"), "") : '';
        };

        dc.getFormattedCourseInstance = function (ci, members) {
            // This is a helper function that formats the CourseInstance metadata
            // and is combination of existing logic in
            // Searchcontroller.courseInstanceToTable and Searchcontroller cell
            // render functions.
            courseInstance = {};
            if (ci) {
                courseInstance['title'] = dc.stripQuotes(ci.title);
                courseInstance['school'] = ci.course ?
                    ci.course.school_id.toUpperCase() : '';
                courseInstance['term'] = ci.term ? ci.term.display_name : '';
                courseInstance['year'] = ci.term ? ci.term.academic_year : '';
                courseInstance['departments'] = ci.course.departments ? ci.course.departments : [];
                courseInstance['course_groups'] = ci.course.course_groups ? ci.course.course_groups : [];
                courseInstance['cid'] = ci.course_instance_id;
                courseInstance['registrar_code_display'] = ci.course ?
                ci.course.registrar_code_display +
                ' (' + ci.course.course_id + ')'.trim() : '';
                courseInstance['description'] = dc.stripQuotes(ci.description);
                courseInstance['short_title'] = dc.stripQuotes(ci.short_title);
                courseInstance['sub_title'] = ci.sub_title ? dc.stripQuotes(ci.sub_title) : '';
                courseInstance['meeting_time'] = ci.meeting_time ? ci.meeting_time : '';
                courseInstance['location'] = ci.location;
                courseInstance['instructors_display'] = ci.instructors_display ? ci.instructors_display : '';
                courseInstance['course_instance_id'] = ci.course_instance_id;
                courseInstance['notes'] = dc.stripQuotes(ci.notes);
                courseInstance['conclude_date'] = ci.conclude_date ? ci.conclude_date : '';

                if (ci.secondary_xlist_instances &&
                    ci.secondary_xlist_instances.length > 0) {
                    courseInstance['xlist_status'] = 'Primary';
                } else if (ci.primary_xlist_instances &&
                    ci.primary_xlist_instances.length > 0) {
                    courseInstance['xlist_status'] = 'Secondary';
                } else {
                    courseInstance['xlist_status'] = 'N/A';
                }

                courseInstance['sites'] = ci.sites ? ci.sites : [];
            }
            courseInstance['members'] = members.count ? members.count : 0;

            return courseInstance;
        };

        dc.courseInstanceId = $routeParams.courseInstanceId;

        dc.setCourseInstance($routeParams.courseInstanceId);

    }
})();
