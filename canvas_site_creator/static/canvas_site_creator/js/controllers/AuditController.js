(function(){
    /**
     * Angular controller for rendering the audit page.
     */
    angular.module('app').controller('AuditController', ['$scope', 'djangoUrl', function($scope, djangoUrl) {
        angular.element(document).ready(function() {
            $scope.dataTable = $('#bulkJobDT').DataTable({
                dom: '<lf<rt>ip>',
                language: {
                    lengthMenu: 'Show _MENU_ bulk jobs',
                    search: 'Search',
                    info: 'Showing _START_ to _END_ of _TOTAL_ bulk jobs',
                    emptyTable: 'There are no bulk jobs to display.'
                },
                order: [[0, 'desc']],
                columns: [
                    {data: 'created_at'},
                    {data: 'status'},
                    {data: 'created_by'},
                    {data: 'count_course_jobs', className: 'dt-body-right'},
                    {data: 'school'},
                    {data: 'term'},
                    {data: 'subaccount'},
                    {data: 'template_canvas_course'}
                ]
            });
        });
    }]);
})();
