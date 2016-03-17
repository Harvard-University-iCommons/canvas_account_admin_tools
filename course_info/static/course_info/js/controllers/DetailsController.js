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
            var peopleResult = results[1];

            //check if the right data was obtained before storing it
            if (courseResult.data.course_instance_id == dc.courseInstanceId) {
                courseInstances.instances[courseResult.data.course_instance_id] = courseResult.data;
                dc.courseInstance = dc.getFormattedCourseInstance(courseResult.data, peopleResult.data)
            } else {
                $log.error(' CourseInstance record mismatch for id :'
                    + dc.courseInstanceId + ',  fetched record for :' + courseResult.data.id);
            }
        };

        dc.setCourseInstance = function (id) {

            var course_url = djangoUrl.reverse(
                'icommons_rest_api_proxy',
                ['api/course/v2/course_instances/' + id + '/']);

            var people_url = djangoUrl.reverse(
                'icommons_rest_api_proxy',
                ['api/course/v2/course_instances/'
                + id + '/people/']);

            var coursePromise = $http.get(course_url)
                .error($scope.handleAjaxError);

            var peoplePromise = $http.get(people_url)
                .error($scope.handleAjaxError);

            $q.all([coursePromise, peoplePromise])
                .then(dc.handleLookupResults);
        };

        dc.stripQuotes = function(str){
            return str ? str.trim().replace(new RegExp("^\"|\"$", "g"), "") : undefined;
        };

        dc.getFormattedCourseInstance = function (ci, people) {
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
                courseInstance['departments'] = ci.course.departments;
                courseInstance['course_groups'] = ci.course.course_groups;
                courseInstance['cid'] = ci.course_instance_id;
                courseInstance['registrar_code_display'] = ci.course ?
                ci.course.registrar_code_display +
                ' (' + ci.course.course_id + ')'.trim() : '';
                courseInstance['description'] = dc.stripQuotes(ci.description);
                courseInstance['short_title'] = dc.stripQuotes(ci.short_title);
                courseInstance['sub_title'] = ci.sub_title;
                courseInstance['meeting_time'] = ci.meeting_time;
                courseInstance['location'] = ci.location;
                courseInstance['instructors_display'] = ci.instructors_display;
                courseInstance['course_instance_id'] = ci.course_instance_id;
                courseInstance['notes'] = dc.stripQuotes(ci.notes);
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
            if(people){
                courseInstance['members'] = people.count;
            }
            return courseInstance;
        };

        dc.courseInstanceId = $routeParams.courseInstanceId;

        dc.setCourseInstance($routeParams.courseInstanceId);

    }
})();
