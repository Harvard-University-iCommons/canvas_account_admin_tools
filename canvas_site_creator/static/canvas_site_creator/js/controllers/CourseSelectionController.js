(function(){
    /**
     * Angular controller for the course selection page of the bulk site creation workflow.
     */
    angular.module('app').controller('CourseSelectionController', ['$scope', 'courseInstanceModel', 'courseInstanceFilterModel', function($scope, courseInstanceModel, courseInstanceFilterModel) {
        $scope.courseInstanceModel = courseInstanceModel;
        $scope.courseInstanceFilterModel = courseInstanceFilterModel;
        $scope.showingSelectedCourses = false;
        $scope.selectedTemplate = $('#templateSelect option').val();
        $scope.confirmationTemplateClause = 'no template';
        $scope.selectedTemplateUrl = '';

        $scope.handleTemplateSelection = function(){
            var $templateOption = $('#templateSelect option:selected');
            $scope.selectedTemplateUrl = $templateOption.data('url');
            $scope.confirmationTemplateClause = 'no template';
            if ($scope.selectedTemplate != 'None') {
                $scope.confirmationTemplateClause = 'template <a href="' + $scope.selectedTemplateUrl + '" target="_blank">' + $templateOption.html() + ' (' + $scope.selectedTemplate + ')</a>';
            }
        };

        $scope.getCreateButtonMessage = function(){
            return $scope.courseInstanceModel.getSelectedCourseIdsCount() ? 'Selected' : 'All';
        };

        $scope.getConfirmationTemplateClause = function(){
            var confirmationTemplateClause = 'no template';
            if ($scope.selectedTemplate != 'None') {
                var $templateOption = $('#templateDropdown option:selected');
                confirmationTemplateClause = 'template <a href="' + $templateOption.data('url') + '" target="_blank">' + $templateOption.html() + ' (' + templateSelection + ')</a>';
            }
            return confirmationTemplateClause;
        };

        $scope.handleCreate = function(){
            $('#createCoursesConfirmed').prop('disabled', true);
            var data = {
                filters: $scope.courseInstanceFilterModel.filters,
                course_instance_ids: Object.keys($scope.courseInstanceModel.selectedCourseInstances),
            };
            if ($scope.selectedTemplate != 'None') {
                data.template = $scope.selectedTemplate;
            }
            $('<input>').attr({
                type: 'hidden',
                id: 'data',
                name: 'data'
            }).val(JSON.stringify(data)).appendTo('#createForm');
            $('#createForm').submit();
        };
    }]);
})();
