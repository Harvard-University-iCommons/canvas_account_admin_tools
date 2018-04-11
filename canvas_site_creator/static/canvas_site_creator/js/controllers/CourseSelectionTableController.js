(function(){
    /**
     * Angular controller for rendering the course selection DataTable.
     */
    angular.module('app').controller('CourseSelectionTableController', ['$scope', 'courseInstanceModel', 'djangoUrl', function($scope, courseInstanceModel, djangoUrl) {
        $scope.courseInstanceModel = courseInstanceModel;

        $scope.renderRemoveColumn = function(data, type, row, meta){
            return '<a href="#" class="remove-selection lti-tooltip" rel="tooltip" data-toggle="tooltip" title="Remove Course" data-original-title="Remove Course"><i class="fa fa-times"></i><span class="sr-only">Remove Course</span></a>';
        };

        $scope.handleRemoveSelection = function(e){
            e.preventDefault();
            var $row = $scope.dataTable.row($(this).closest('tr'));
            $scope.courseInstanceModel.removeSelectedCourseInstance($row.data());
            $scope.$apply();
        };

        $scope.reloadDataTable = function() {
            $scope.dataTable
                .clear()
                .page(0)
                .search('')
                .rows.add($scope.courseInstanceModel.getSelectedCourses())
                .draw();
        };

        angular.element(document).ready(function() {
            $scope.dataTable = $('#courseSelectionDT').DataTable({
                dom: '<f<rt>ip>',
                language: {
                    search: 'Search',
                    info: 'Showing _START_ to _END_ of _TOTAL_ courses',
                    emptyTable: 'There are no courses to display.'
                },
                pageLength: 5,
                data: $scope.courseInstanceModel.getSelectedCourses(),
                order: [[3, 'asc']],
                columns: [
                    {data: 'id', orderable: false, className: 'col-align-center', render: $scope.renderRemoveColumn},
                    {data: 'id'},
                    {data: 'registrar_code'},
                    {data: 'title'},
                    {data: 'course_section', className: 'col-align-center'},
                ],
                preDrawCallback: function(){
                    $('#courseSelectionDT .remove-selection').off('click', $scope.handleRemoveSelection);
                },
                drawCallback: function(){
                    $('#courseSelectionDT .remove-selection').on('click', $scope.handleRemoveSelection);
                }
            });

            $scope.$watch('courseInstanceModel.selectedCourseInstances', $scope.reloadDataTable, true);
        });

        $('body').tooltip({
            selector: '[rel=tooltip]'
        });
        $('[rel=tooltip]').tooltip({
            container: 'body'
        });
    }]);
})();
