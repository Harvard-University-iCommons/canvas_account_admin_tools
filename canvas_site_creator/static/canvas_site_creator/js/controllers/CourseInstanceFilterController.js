(function(){
    /**
     * Angular controller for displaying dropdowns which allow you to select school, term, department,
     * and course group for filtering course instance queries.
     */
    angular.module('app').controller('CourseInstanceFilterController', ['$scope', 'courseInstanceFilterModel', function($scope, courseInstanceFilterModel){
        $scope.courseInstanceFilterModel = courseInstanceFilterModel;

        $scope.handleSchoolSelected = function(){
            // When a school is selected, go get the other filter options from the server
            // Otherwise, clear the other filter options out
            if ($scope.courseInstanceFilterModel.getSelectedFilterId('school')) {
                $scope.courseInstanceFilterModel.loadFilterOptions('term');
                if (!$scope.courseInstanceFilterModel.disabled.department) {
                    $scope.courseInstanceFilterModel.loadFilterOptions('department');
                }
                if (!$scope.courseInstanceFilterModel.disabled.course_group) {
                    $scope.courseInstanceFilterModel.loadFilterOptions('course_group');
                }
            } else {
                $scope.courseInstanceFilterModel.filters.term = '';
                $scope.courseInstanceFilterModel.filters.department = '';
                $scope.courseInstanceFilterModel.filters.course_group = '';
                $scope.courseInstanceFilterModel.terms = [];
                $scope.courseInstanceFilterModel.departments = [];
                $scope.courseInstanceFilterModel.course_groups = [];
            }
        };

        $scope.showFilter = function(parentFilterType, filterType){
            // Show the filter dropdown if the previous filter option has a selection and
            // this filter option has options
            return $scope.courseInstanceFilterModel.getSelectedFilterId(parentFilterType) &&
                $scope.courseInstanceFilterModel.filterOptions[filterType].length > 1;
        };
    }]);
})();
