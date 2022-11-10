(function(){
    /**
     * Angular controller for rendering the course instance DataTable.
     */
    angular.module('app').controller('CourseInstanceController', ['$scope', 'courseInstanceModel', 'courseInstanceFilterModel', 'djangoUrl', function($scope, courseInstanceModel, courseInstanceFilterModel, djangoUrl) {
        $scope.courseInstanceModel = courseInstanceModel;
        $scope.courseInstanceFilterModel = courseInstanceFilterModel;
        $scope.selectAll = false;

        $scope.renderSelectionColumn = function(data, type, row, meta){
            return '<input type="checkbox" class="col-select" data-course_instance_id="' + data + '"/>';
        };

        $scope.toggleSelectAll = function(){
            $scope.selectAll = !$scope.selectAll;
            $('#courseInstanceDT tbody tr').each(function(index, tr){
                var $checkbox = $(tr).find('.col-select');
                $checkbox.prop('checked', $scope.selectAll);
                if ($scope.selectAll) {
                    $scope.courseInstanceModel.addSelectedCourseInstance($scope.dataTable.row(index).data());
                } else {
                    $scope.courseInstanceModel.removeSelectedCourseInstance($scope.dataTable.row(index).data());
                }
            });
        };

        $scope.syncSelectionCheckboxes = function(){
            $('#courseInstanceDT tbody .col-select').each(function(o) {
                var $checkbox = $(this);
                var courseInstanceId = $checkbox.data('course_instance_id');
                var isSelected = Boolean($scope.courseInstanceModel.selectedCourseInstances[courseInstanceId]);
                $checkbox.closest('tr').toggleClass('selected', isSelected);
                $checkbox.prop('checked', isSelected);
            });
            $scope.selectAll = !$('#courseInstanceDT tbody tr').not('.selected').length;
        };

        $scope.$watch('courseInstanceModel.selectedCourseInstances', $scope.syncSelectionCheckboxes, true);

        $scope.handleRowClick = function(e){
            var $tr = $(e.target).closest('tr');
            var selected = !$tr.hasClass('selected');
            var courseInstanceData = $scope.dataTable.row($tr).data();
            if (selected) {
                $scope.courseInstanceModel.addSelectedCourseInstance(courseInstanceData);
            } else {
                $scope.courseInstanceModel.removeSelectedCourseInstance(courseInstanceData);
            }
            $scope.$apply();
        };

        var accountFilterId = $scope.courseInstanceFilterModel.getAccountFilterId();
        angular.element(document).ready(function() {
            $scope.dataTable = $('#courseInstanceDT').DataTable({
                serverSide: true,
                deferRender: true,
                processing: true,
                searchDelay: 3000,
                dom: '<lf<rt>ip>',
                language: {
                    lengthMenu: 'Show _MENU_ courses',
                    processing: '<img src="https://static.tlt.harvard.edu/shared/images/ajax-loader-small.gif" class="loading"/> Searching...',
                    search: 'Search by Course Code, Course Title or SIS ID',
                    info: 'Showing _START_ to _END_ of _TOTAL_ courses',
                    emptyTable: 'There are no courses to display.'
                },
                ajax: {
                    url: djangoUrl.reverse('canvas_site_creator:api_course_instances', [$scope.courseInstanceFilterModel.filters.term, accountFilterId]),
                    type: 'GET',
                    data: $scope.courseInstanceFilterModel.filters,
                    dataSrc: function(json) {
                        $scope.courseInstanceModel.dataLoaded = true;
                        $scope.courseInstanceModel.totalCourses = json.recordsTotal;
                        $scope.courseInstanceModel.totalCoursesWithCanvasSite = json.recordsTotalWithCanvasSite;
                        $scope.courseInstanceModel.totalCoursesWithoutCanvasSite = json.recordsTotalWithoutCanvasSite;
                        $scope.courseInstanceModel.totalCoursesWithExternalSite = json.recordsTotalExternalSite;
                        $scope.courseInstanceModel.totalCoursesWithExternalSiteOfficial = json.recordsTotalExternalSiteOfficial;
                        $scope.$apply();
                        return json.data;
                    }
                },
                order: [[3, 'asc']],
                columns: [
                    {data: 'id', orderable: false, className: 'col-align-center', render: $scope.renderSelectionColumn},
                    {data: 'id'},
                    {data: 'registrar_code'},
                    {data: 'title'},
                    {data: 'course_section', className: 'col-align-center'},
                ],
                preDrawCallback: function(){
                    $scope.courseInstanceModel.dataLoading = true;
                    $('#courseInstanceDT tbody tr').off('click', $scope.handleRowClick);
                },
                drawCallback: function(){
                    $scope.courseInstanceModel.dataLoading = false;
                    $scope.syncSelectionCheckboxes();
                    $scope.$apply();  // otherwise UI selectAll checkbox will not reflect scope changes
                    $('#courseInstanceDT tbody tr').on('click', $scope.handleRowClick);
                }
            });
        });
    }]);
})();
