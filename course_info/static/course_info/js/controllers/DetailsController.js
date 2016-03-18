// TODO - this is pretty much a copy of the people controller with some mods.
// TODO - this still needs a lot of clean up, we don't need everything in here

(function () {
    var app = angular.module('CourseInfo');
    app.controller('DetailsController', DetailsController);

    function DetailsController($scope, $routeParams, courseInstances, $compile,
                               djangoUrl, $http, $q, $log, $uibModal, $sce) {

        var dc = this;

        var remove_quotes_regex = new RegExp("^\"|\"$", "g");

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

        //dc.stripQuotes = function(str){
        //    // soem fields are coming over with quotes around them and those quotes
        //    // are being displayed in the html.
        //    // This strips off double quotes from the begining and ending of fields
        //    return str ? str.trim().replace(remove_quotes_regex, "") : '';
        //};

        dc.getFormattedCourseInstance = function (ci, members) {
            // This is a helper function that formats the CourseInstance metadata
            // and is combination of existing logic in
            // Searchcontroller.courseInstanceToTable and Searchcontroller cell
            // render functions.
            courseInstance = {};
            if (ci) {
                courseInstance['title'] = ci.title;
                courseInstance['school'] = ci.course.school_id.toUpperCase();
                courseInstance['term'] = ci.term.display_name;
                courseInstance['year'] = ci.term.academic_year;
                courseInstance['departments'] = ci.course.departments;
                courseInstance['course_groups'] = ci.course.course_groups;

                var registrar_code = ci.course.registrar_code_display ? ci.course.registrar_code_display : ci.course.registrar_code;

                courseInstance['registrar_code_display'] = registrar_code + ' (' + ci.course.course_id + ')'.trim();

                courseInstance['description'] = ci.description;
                courseInstance['short_title'] = ci.short_title;
                courseInstance['sub_title'] = ci.sub_title;
                courseInstance['meeting_time'] = ci.meeting_time;
                courseInstance['location'] = ci.location;
                courseInstance['instructors_display'] = ci.instructors_display;
                courseInstance['course_instance_id'] = ci.course_instance_id;
                courseInstance['notes'] = ci.notes;
                courseInstance['conclude_date'] = ci.conclude_date;

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
            courseInstance['members'] = members.count;

            return courseInstance;
        };

        dc.courseInstanceId = $routeParams.courseInstanceId;

        dc.setCourseInstance($routeParams.courseInstanceId);

    }
})();
