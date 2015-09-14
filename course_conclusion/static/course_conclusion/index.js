// TODO - add .error() methods to all ajax calls

(function () {
    var app = angular.module('courseConclusionApp', ['ui.bootstrap']);

    app.controller('CourseConclusionController',
                   ['$http', '$filter', function($http, $filter) {
        var baseUrl = COURSE_CONCLUSION_API_URL;
        var ctrl = this;
        ctrl.FIVE_HOURS_IN_MSEC = 12 * 60 * 60 * 1000;

        // objects backing the selects on the page
        ctrl.schools = [];
        ctrl.terms = [];
        ctrl.courses = [];
        ctrl.concluded_courses = [];


        // models matching the current selections on the page
        ctrl.currentSchool = null;
        ctrl.currentTerm = null;
        ctrl.currentCourse = null;
        ctrl.currentConcludeDate = null;

        // keep track of alerts from the form
        ctrl.alerts = [];

        // take care of xsrf protection before we make $http calls
        $http.defaults.xsrfCookieName = 'csrftoken';
        $http.defaults.xsrfHeaderName = 'X-CSRFToken';

        // go get the list of schools once
        $http.get(baseUrl + 'schools').success(function(data) {
            ctrl.schools = data;
            //If there is only one school, pre-select it and render the concluded courses for that school
            if (ctrl.schools.length==1) {
                ctrl.currentSchool =  ctrl.schools[0];
                ctrl.getConcludedCourses();
            }
        });

        //gets the list of concluded courses for a school
        ctrl.getConcludedCourses = function() {
            ctrl.concluded_courses = [];
            if (ctrl.currentSchool) {
                var url = baseUrl + 'concluded_courses_by_school?school_id=' + ctrl.currentSchool.school_id;
                $http.get(url).success(function (data) {
                    ctrl.concluded_courses = data;
                });
            }
        };

        //gets the list of concluded courses for a school and a term
        ctrl.getConcludedCoursesBySchoolTerm= function() {
            ctrl.concluded_courses = [];
            if (ctrl.currentSchool && ctrl.currentTerm) {
                var url = baseUrl + 'concluded_courses_by_school_term'
                    + '?school_id=' + ctrl.currentSchool.school_id
                    + '&term_id=' + ctrl.currentTerm.term_id;
                $http.get(url).success(function (data) {
                    ctrl.concluded_courses = data;
                });
            }
        };
        // gets the list of terms for a school
        ctrl.getTerms = function() {
            ctrl.terms = [];
            ctrl.courses = [];
            ctrl.currentTerm = null;
            ctrl.currentCourse = null;
            ctrl.currentConcludeDate = null;
            if (ctrl.currentSchool) {
                var url = baseUrl + 'terms?school_id=' + ctrl.currentSchool.school_id;
                $http.get(url).success(function (data) {
                    ctrl.terms = data;
                });
            }
        };

        // gets the list of courses for a school and term
        ctrl.getCourses = function() {
            ctrl.courses = [];
            ctrl.currentCourse = null;
            ctrl.currentConcludeDate = null;

            if (ctrl.currentSchool && ctrl.currentTerm){
                var url = baseUrl + 'courses'
                    + '?school_id=' + ctrl.currentSchool.school_id
                    + '&term_id=' + ctrl.currentTerm.term_id;
                $http.get(url).success(function (data) {
                    ctrl.courses = data;
                });
            }
        };

        // submits the current course's conclude_date to the server
        ctrl.submit = function(form) {
            var url = baseUrl + 'courses/' + ctrl.currentCourse.course_instance_id;
            var data = {
                course_instance_id: ctrl.currentCourse.course_instance_id,
                conclude_date: ctrl.currentConcludeDate,
            };
            $http.patch(url, data)
                .success(function(data) {
                    var msg = 'Conclude date for course "' + data.title + '" ';
                    if (data.conclude_date) {
                        // should be the same as conclude_date, but just in case
                        msg += 'set to ' + ctrl.currentConcludeDate;
                    }
                    else {
                        msg += 'removed';
                    }
                    ctrl.currentCourse.conclude_date = data.conclude_date;
                    ctrl.addAlert({type: 'success', msg: msg});
                    ctrl.concluded_courses = ctrl.getConcludedCoursesBySchoolTerm();
                })
                .error(function(data) {
                    ctrl.addAlert({type: 'error', msg: data.error});
                });
        };

        //checks if there are multiple schools in the schools list
        ctrl.hasMultipleSchools = function(){
            if (ctrl.schools.length>1) {
                return true;
            }
            return false;
        }


        ctrl.reset = function(form) {
            ctrl.terms = [];
            ctrl.courses = [];
            ctrl.currentSchool = null;
            ctrl.currentTerm = null;
            ctrl.currentCourse = null;
            ctrl.currentConcludeDate = null;
            ctrl.concluded_courses = []
        };

        ctrl.addAlert = function (alert) {
            ctrl.alerts.push(alert);
        };

        ctrl.closeAlert = function(index) {
            ctrl.alerts.splice(index, 1);
        };
    }]);
})();
