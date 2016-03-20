(function () {
    var app = angular.module('CourseInfo');
    app.controller('DetailsController', DetailsController);
    app.directive('huEditableField', editableFieldDirective);
    app.directive('huFieldLabelWrapper', fieldLabelWrapperDirective);

    function DetailsController($scope, $routeParams, courseInstances, $compile,
                               djangoUrl, $http, $q, $log, $uibModal, $sce) {

        var dc = this;
        dc.courseDetailsUpdateInProgress = false;
        dc.courseInstanceId = $routeParams.courseInstanceId;
        dc.courseInstance = {};
        dc.courseInstances = courseInstances;
        dc.editable = false;

        dc.init = function() {
            var instances = courseInstances.instances;
            if (instances && instances[dc.courseInstanceId]) {
                dc.courseInstance = dc.getFormattedCourseInstance(
                    instances[dc.courseInstanceId]);
            }
            dc.fetchCourseInstanceDetails(dc.courseInstanceId);
        };

        dc.handleAjaxErrorResponse = function(r) {
            dc.handleAjaxError(
                r.data, r.status, r.headers, r.config, r.statusText);
        };

        dc.handleAjaxError = function (data, status, headers, config, statusText) {
            $log.error('Error attempting to ' + config.method + ' ' + config.url +
                ': ' + status + ' ' + statusText + ': ' + JSON.stringify(data));
        };

        dc.isCourseInstanceEditable = function(courseRegistrarCode) {
            return (courseRegistrarCode.startsWith('ILE-') ||
                    courseRegistrarCode.startsWith('SB-'));
        };

        dc.handleCourseInstanceResponse = function(response) {
            //check if the right data was obtained before storing it
            if (response.data.course_instance_id == dc.courseInstanceId) {
                courseInstances.instances[response.data.course_instance_id] = response.data;
                // if people/members are fetched first, we don't want to
                // overwrite the members attribute of dc.courseInstance
                $.extend(dc.courseInstance,
                    dc.getFormattedCourseInstance(response.data));
                // todo: comment
                // using 354962 for ILE testing
                var rc = response.data.course.registrar_code;
                dc.editable = dc.isCourseInstanceEditable(rc);
                dc.resetForm();
            } else {
                $log.error(' CourseInstance record mismatch for id :'
                    + dc.courseInstanceId + ',  fetched record for :'
                    + response.data.id);
            }
        };

        dc.handlePeopleResponse = function(response) {
            if (!dc.hasOwnProperty('courseInstance')) { }
            dc.courseInstance['members'] = response.data.count;
        };

        dc.fetchCourseInstanceDetails = function (id) {

            var course_url = djangoUrl.reverse(
                'icommons_rest_api_proxy',
                ['api/course/v2/course_instances/' + id + '/']);

            var members_url = djangoUrl.reverse(
                'icommons_rest_api_proxy',
                ['api/course/v2/course_instances/'
                + id + '/people/']);

            $http.get(course_url)
                .then(dc.handleCourseInstanceResponse,
                    dc.handleAjaxErrorResponse);

            $http.get(members_url)
                .then(dc.handlePeopleResponse,
                    dc.handleAjaxErrorResponse);

        };

        dc.getFormattedCourseInstance = function (ciData) {
            // This is a helper function that formats the CourseInstance metadata
            // and is combination of existing logic in
            // Searchcontroller.courseInstanceToTable and Searchcontroller cell
            // render functions.
            var ci = ciData;  // shorten for brevity, preferable to `with()`
            var courseInstance = {};
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

            return courseInstance;
        };

        // todo - fix pristine?
        dc.resetForm = function() {
            dc.formDisplayData = angular.copy(dc.courseInstance);
        };

        // todo: data validation
        dc.submitCourseDetailsForm = function() {
            dc.courseDetailsUpdateInProgress = true;
            var postData = {};
            var url = djangoUrl.reverse('icommons_rest_a' +
                'pi_proxy',
                ['api/course/v2/course_instances/'
                + dc.courseInstanceId + '/']);
            var fields = [
                'description',
                'instructors_display',
                'location',
                'meeting_time',
                'notes',
                'short_title',
                'sub_title',
                'title'
            ];
            fields.forEach(function(field) {
                postData[field] = dc.formDisplayData[field];
            });

            // todo: refactor and collapse, no longer need all these functions since they are single-line
            $http.patch(url, postData)
                .then(function finalizeCourseDetailsPatch(response) {
                    // update Reset button
                    $.extend(dc.courseInstance, postData);
                }, dc.handleAjaxError)
                .finally( function courseDetailsUpdateNoLongerInProgress() {
                    dc.courseDetailsUpdateInProgress = false;
                });
        };

        dc.init();
    }

    function editableFieldDirective() {
        return {
            //templateUrl: 'directives/editable_field.html'
            scope: {
                editable: '=', // can be < in angular 1.5
                field: '@',
                formValue: '=',
                label: '@',
                modelValue: '=',
            },
            template: ' \
<li class="list-group-item"> \
  <div class="form-group"> \
    <label for="input-course-{{field}}" class="col-md-2"> \
      {{label}} \
    </label> \
    <div class="col-md-10"> \
      <input type="text" class="form-control" id="input-course-{{field}}" ng-show="editable" ng-model="formValue"/> \
      <span ng-hide="editable">{{modelValue}}</span> \
    </div> \
  </div> \
</li> \
'
        }
    }

    function fieldLabelWrapperDirective() {
        return {
            //templateUrl: 'directives/field_label_wrapper.html'
            scope: {
                field: '@',
                label: '@',
            },
            transclude: true,
            template: ' \
<li class="list-group-item"> \
  <div class="form-group"> \
    <label for="input-course-{{field}}" class="col-md-2"> \
      {{label}} \
    </label> \
    <div class="col-md-10" ng-transclude> \
    </div> \
  </div> \
</li> \
'
        }
    }

})();
