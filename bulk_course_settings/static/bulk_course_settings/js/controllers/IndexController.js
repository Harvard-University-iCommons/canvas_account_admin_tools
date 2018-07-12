(function(){
    /**
     * Angular controller for the home page of bulk_course_settings.
     *
     * Handles navigation to step 1 of the bulk site creation workflow,
     * adding course instance filter values to the request so that they
     * can be used to bootstrap step 1.
     */
    angular.module('app').controller('IndexController', ['$scope', 'courseInstanceFilterModel', 'courseInstanceModel', function($scope, courseInstanceFilterModel, courseInstanceModel){
        $scope.courseInstanceFilterModel = courseInstanceFilterModel;
        $scope.courseInstanceModel = courseInstanceModel;

        $scope.showSummaryLoading = function(){
            return $scope.courseInstanceModel.dataLoading;
        };

        $scope.showSummary = function(){
            return !$scope.courseInstanceModel.dataLoading && $scope.courseInstanceModel.dataLoaded &&
                $scope.courseInstanceFilterModel.getSelectedFilterId('term');
        };

        $scope.createDisabled = function(){
            // Disable create button if there are no course instances in the selected filters,
            // the user hasn't selected a term, or we are in the midst of loading course summary data
            return !$scope.courseInstanceModel.totalCoursesWithoutCanvasSite ||
                !$scope.courseInstanceFilterModel.getSelectedFilterId('term') ||
                $scope.courseInstanceModel.dataLoading;
        };

        $scope.handleCreate = function(e){
            e.preventDefault();
            var params = {
                school: $scope.courseInstanceFilterModel.getSelectedFilterId('school'),
                term: $scope.courseInstanceFilterModel.getSelectedFilterId('term'),
                department: $scope.courseInstanceFilterModel.getSelectedFilterId('department'),
                course_group: $scope.courseInstanceFilterModel.getSelectedFilterId('course_group')
            };
            window.location = $(e.target).data('href') + '&' + $.param(params);
        };

        $scope.courseInstanceFilterModel.initFilterOptions();
        courseInstanceModel.loadCourseInstanceSummary(true);

        // Watch the course instance filters and load the course instance summary when they change
        $scope.$watch('courseInstanceFilterModel.filters.school', $scope.courseInstanceModel.initSummaryData);
        $scope.$watch('courseInstanceFilterModel.filters.term', $scope.courseInstanceModel.loadCourseInstanceSummary);
        $scope.$watch('courseInstanceFilterModel.filters.department', $scope.courseInstanceModel.loadCourseInstanceSummary);
        $scope.$watch('courseInstanceFilterModel.filters.course_group', $scope.courseInstanceModel.loadCourseInstanceSummary);
    }]);
})();
