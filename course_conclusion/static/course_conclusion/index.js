(function () {
    var app = angular.module('courseConclusionApp', []);

    app.controller('CourseConclusionController', function($scope, $http) {
        var base_url = '/tools/course_conclusion/api/'; // TODO - don't harcode
        var ctrl = this;

        // objects backing the selects on the page
        ctrl.schools = [];
        ctrl.terms = [];
        ctrl.courses = [];

        // models matching the current selections on the page
        ctrl.currentSchool = '';
        ctrl.currentTerm = '';
        ctrl.currentCourse = '';
        ctrl.currentConclusionDate = '';

        // get the list of schools
        $http.get(base_url + 'schools').success(function(data) {
            ctrl.schools = data;
        });

        // get the list of terms for a school
        ctrl.getTerms = function() {
            ctrl.terms = {};
            ctrl.courses = {};
            ctrl.currentTerm = '';
            ctrl.currentCourse = '';

            var url = base_url + 'terms?school_id=' + ctrl.currentSchool;
            $http.get(url).success(function(data) {
                ctrl.terms = data.reduce(function(map, term) {
                    map[term.term_id] = term;
                    return map;
                }, {});
            });
        };

        // get the list of courses for a school and term
        ctrl.getCourses = function() {
            ctrl.courses = {};
            ctrl.currentCourse = '';

            var url = base_url + 'courses'
                      + '?school_id=' + ctrl.currentSchool
                      + '&term_id=' + ctrl.currentTerm;
            $http.get(url).success(function(data) {
                ctrl.courses = data.reduce(function(map, course) {
                    map[course.course_instance_id] = course;
                    return map;
                }, {});
            });
        };
    });
})();
