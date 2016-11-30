(function(){
    /**
     * Angular service for sharing data needed for rendering and controlling bulk job detail data across controllers.
     */
    angular.module('app').factory('bulkJobDetailModel', [function(){
        return {
            totalCourseJobs: 0,
            completeCourseJobs: 0,
            successfulCourseJobs: 0,
            failedCourseJobs: 0,
            percentageComplete: 0
        };
    }]);
})();
