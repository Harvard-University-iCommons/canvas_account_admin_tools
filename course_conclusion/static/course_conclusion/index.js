// TODO - add .error() methods to all ajax calls

(function () {
    var app = angular.module('courseConclusionApp', ['ui.bootstrap']);

    app.controller('CourseConclusionController',
                   ['$http', '$filter', function($http, $filter) {
        var baseUrl = COURSE_CONCLUSION_API_URL;
        var ctrl = this;

        // objects backing the selects on the page
        ctrl.schools = [];
        ctrl.terms = [];
        ctrl.courses = {};

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
        });

        // gets the list of terms for a school
        ctrl.getTerms = function() {
            ctrl.terms = [];
            ctrl.courses = {};
            ctrl.currentTerm = null;
            ctrl.currentCourse = null;
            ctrl.currentConcludeDate = null;

            var url = baseUrl + 'terms?school_id=' + ctrl.currentSchool.school_id;
            $http.get(url).success(function(data) {
                ctrl.terms = data;
            });
        };

        // gets the list of courses for a school and term
        ctrl.getCourses = function() {
            ctrl.courses = {};
            ctrl.currentCourse = null;
            ctrl.currentConcludeDate = null;

            var url = baseUrl + 'courses'
                      + '?school_id=' + ctrl.currentSchool.school_id
                      + '&term_id=' + ctrl.currentTerm.term_id;
            $http.get(url).success(function(data) {
                var courses = data.reduce(function(map, course) {
                    if (course.conclude_date) {
                        course.conclude_date = new Date(course.conclude_date);
                    }
                    map[course.course_instance_id] = course;
                    return map;
                }, {});
                ctrl.courses = courses;
            });
        };

        // for some reason this didn't work as an expression for ng-disabled
        ctrl.hasCourses = function() {
            return Object.keys(ctrl.courses).length > 0;
        }

        // submits the current course's conclude_date to the server
        ctrl.submit = function(form) {
            var url = baseUrl + 'courses/' + ctrl.currentCourse.course_instance_id;
            var conclude_date = $filter('date')(ctrl.currentConcludeDate,
                                                'yyyy-MM-dd');
            var data = {
                course_instance_id: ctrl.currentCourse.course_instance_id,
                conclude_date: conclude_date,
            };
            $http.patch(url, data)
                .success(function(data) {
                    console.log('success');
                    var msg = 'Conclude date for course "' + data.title + '" ';
                    if (data.conclude_date) {
                        // should be the same as conclude_date, but just in case
                        var response_conclude_date = $filter('date')(
                                                         data.conclude_date,
                                                         'yyyy-MM-dd');
                        msg += 'set to ' + conclude_date;
                    }
                    else {
                        msg += 'removed';
                    }
                    ctrl.addAlert({type: 'success', msg: msg});
                    ctrl.courses[data.course_instance_id].conclude_date = 
                        data.conclude_date;
                })
                .error(function(data) {
                    ctrl.addAlert({type: 'error', msg: data.error});
                });
        };


        ctrl.reset = function(form) {
            ctrl.terms = [];
            ctrl.courses = {};
            ctrl.currentSchool = null;
            ctrl.currentTerm = null;
            ctrl.currentCourse = null;
            ctrl.currentConcludeDate = null;
        };

        ctrl.addAlert = function (alert) {
            ctrl.alerts.push(alert);
        };

        ctrl.closeAlert = function(index) {
            ctrl.alerts.splice(index, 1);
        };
    }]);
})();
