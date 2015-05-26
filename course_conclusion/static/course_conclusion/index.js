var courseConclusionApp = angular.module('courseConclusionApp', []);

courseConclusionApp.controller('CourseConclusionController', function($scope, $http) {
    $scope.schools = [];
    $http.get('/tools/course_conclusion/api/schools').success(function(data) {
        var schools = [{'label': 'Select a School', 'value': ''}];
        $scope.schools = schools.concat(data.map(function(school) {
            return {'value': school.school_id,
                    'label': school.title_short + ' (' 
                             + school.school_id.toUpperCase() + ')'};
        }));
    });
    $scope.schoolProp = '';

    $scope.term_temps = ['Spring 2015', 'Summer 2015', 'Fall 2015'];
    $scope.terms = [];
    $scope.termProp = '';

    $scope.course_temps = ['Bio 101', 'Chem 100', 'Phys 102'];
    $scope.courses = [];
    $scope.courseProp = '';

    $scope.fillTerms = function() {
        $scope.terms = [''].concat($scope.term_temps.map(function(tt) {
                       return $scope.schoolProp + ' ' + tt;
                   }));
    };

    $scope.fillCourses = function() {
        $scope.courses = [''].concat($scope.course_temps.map(function(ct) {
                         return $scope.termProp + ' ' + ct;
                     }));
    }

});
