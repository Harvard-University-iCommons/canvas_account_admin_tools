(function(){
    /**
     * Angular controller for rendering the course job DataTable and bulk job progress indicators.
     */
    angular.module('app').controller('BulkJobDetailController', ['$scope', 'bulkJobDetailModel', '$interval', 'djangoUrl', function($scope, bulkJobDetailModel, $interval, djangoUrl) {
        $scope.bulkJobDetailModel = bulkJobDetailModel;
        $scope.AUTO_REFRESH_INTERVAL = 20000;  // For automatically refreshing the DataTable
        $scope.bulkJobId = $('#courseJobDT').data('bulk_job_id');
        $scope.dataLoaded = false;

        $scope.renderTitleColumn = function(data, type, row, meta){
            var column = data;
            if (row.canvas_course_id) {
                column = '<a href="' + window.globals.CANVAS_URL + '/courses/' + row.canvas_course_id + '" target="_blank">' + data + '</a>';
            }
            return column;
        };

        $scope.showProgress = function(){
            return $scope.dataLoaded;
        };

        $scope.getProgressBarStyle = function(){
            return {width: $scope.bulkJobDetailModel.percentageComplete + '%'};
        };

        var stop;
        $scope.startAutoRefresh = function(){
            stop = $interval(function(){
                $scope.dataTable.ajax.reload(null, false);
            }, $scope.AUTO_REFRESH_INTERVAL);
        };

        $scope.stopAutoRefresh = function(){
            $interval.cancel(stop);
            stop = undefined;
        };

        angular.element(document).ready(function() {
            $scope.dataTable = $('#courseJobDT').DataTable({
                serverSide: true,
                deferRender: true,
                processing: true,
                searchDelay: 3000,
                dom: '<l<rt>ip>',
                language: {
                    lengthMenu: 'Show _MENU_ jobs',
                    processing: '<img src="https://static.tlt.harvard.edu/shared/images/ajax-loader-small.gif" class="loading"/> Searching...',
                    search: 'Search',
                    info: 'Showing _START_ to _END_ of _TOTAL_ jobs',
                    emptyTable: 'There are no course site creation jobs to display.'
                },
                ajax: {
                    url: djangoUrl.reverse('canvas_site_creator:api_course_jobs', [$scope.bulkJobId]),
                    type: 'GET',
                    dataSrc: function(json) {
                        $scope.dataLoaded = true;
                        $scope.bulkJobDetailModel.totalCourseJobs = json.recordsTotal;
                        $scope.bulkJobDetailModel.completeCourseJobs = json.recordsComplete;
                        $scope.bulkJobDetailModel.successfulCourseJobs = json.recordsSuccessful;
                        $scope.bulkJobDetailModel.failedCourseJobs = json.recordsFailed;
                        $scope.bulkJobDetailModel.percentageComplete = Math.round((json.recordsComplete/json.recordsTotal) * 100);
                        if ($scope.bulkJobDetailModel.percentageComplete == 100) {
                            // The bulk job is done, so stop auto refresh
                            $scope.stopAutoRefresh();
                        }
                        $scope.$apply();
                        return json.data;
                    }
                },
                order: [[0, 'desc']],
                columns: [
                    {data: 'created_at'},
                    {data: 'status'},
                    {data: 'created_by', orderable: false},
                    {data: 'sis_course_id', orderable: false},
                    {data: 'registrar_code', orderable: false},
                    {data: 'course_title', orderable: false, render: $scope.renderTitleColumn}
                ],
                initComplete: function(){
                    if (!$('#courseJobDT').data('bulk_job_complete')) {
                        $scope.startAutoRefresh();
                    }
                }
            });
        });
    }]);
})();
