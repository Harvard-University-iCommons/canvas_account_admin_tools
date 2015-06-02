var courseConclusionApp = angular.module('courseConclusionApp', []);

courseConclusionApp.controller('CourseConclusionController', function($scope, $http) {
    var base_url = '/tools/course_conclusion/api/';

    $scope.schools = [];
    $http.get(base_url + 'schools').success(function(data) {
        var schools = [{'label': 'Select a School', 'value': ''}];
        $scope.schools = schools.concat(data.map(function(school) {
            return {'value': school.school_id,
                    'label': school.title_short + ' (' 
                             + school.school_id.toUpperCase() + ')'};
        }));
    });
    $scope.schoolProp = '';

    $scope.terms = [];
    $scope.termProp = '';

    $scope.courses = [];
    $scope.courseProp = '';

    $scope.fillTerms = function() {
        $scope.terms = [];
        $scope.termProp = '';
        $scope.courses = [];
        $scope.courseProp = '';

        var url = base_url + 'terms?school_id=' + $scope.schoolProp;
        $http.get(url).success(function(data) {
            var terms = [{'label': 'Select a Term', 'value': ''}];
            $scope.terms = terms.concat(data.map(function(term) {
                return {'value': term.term_id,
                        'label': term.display_name};
            }));
        });
    };

    $scope.fillCourses = function() {
        $scope.courses = [];
        $scope.courseProp = '';
        var url = base_url + 'courses?school_id=' + $scope.schoolProp
                           + '&term_id=' + $scope.termProp;
        $http.get(url).success(function(data) {
            var courses = [{'label': 'Select a Course', 'value': ''}];
            $scope.courses = courses.concat(data.map(function(course) {
                return {'value': course.course_instance_id,
                        'label': course.short_title};
            }));
        });
    }
});
