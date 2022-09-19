(function(){
    /**
     * Angular service for sharing data needed for rendering and controlling the display of course instances
     * across controllers.
     */
    angular.module('app').factory('courseInstanceModel', [
            '$http', 'djangoUrl', 'errorModel', 'courseInstanceFilterModel', '$q', '$log',
            function($http, djangoUrl, errorModel, courseInstanceFilterModel, $q, $log){
        var self = {};
        self.dataLoading = false;
        self.dataLoaded = false;
        // keeps track of the most recent course instance summary $http.get()
        // timeout/cancellation promise so we can cancel it if a change is made
        // to the course instance summary filter params before we've updated the
        // UI with information from the existing, in-process request
        self.pendingCancel = null;  // tracks a Deferred object
        self.selectedCourseInstances = {};

        self.initSummaryData = function(){
            self.totalCourses= 0;
            self.totalCoursesWithCanvasSite= 0;
            self.totalCoursesWithCanvasSiteWithExternal = 0;
            self.totalCoursesWithoutCanvasSite= 0;
            self.totalCoursesWithoutCanvasSiteWithExternal = 0;
            self.totalCoursesWithoutCanvasSiteAndSyncToCanvasFalse = 0
            self.totalCoursesWithoutCanvasSiteAndSyncToCanvasFalseWithExternal = 0
        };
        self.initSummaryData();

        self.addSelectedCourseInstance = function(courseInstanceData){
            self.selectedCourseInstances[courseInstanceData['id']] = courseInstanceData;
        };

        self.removeSelectedCourseInstance = function(courseInstanceData){
            delete self.selectedCourseInstances[courseInstanceData['id']];
        };

        self.getSelectedCourseIdsCount = function(){
            return Object.keys(self.selectedCourseInstances).length;
        };

        self.getSelectedCourses = function(){
            return Object.keys(self.selectedCourseInstances).map(function(key){
                return self.selectedCourseInstances[key];
            })
        };

        self.loadCourseInstanceSummary = function(newFilterValue, oldFilterValue){
            // these get included when triggered by $watch(); if this function
            // is called manually, simply calling with
            // loadCourseInstanceSummary(true) should be enough to create a new
            // request
            if (newFilterValue == oldFilterValue) { return; }

            var selectedTermId = courseInstanceFilterModel.getSelectedFilterId('term');
            if (!selectedTermId) { return; }

            var selectedAccountId = courseInstanceFilterModel.getAccountFilterId();
            if (self.dataLoading && self.pendingCancel) {
                // data still loading from previous request, cancel it
                self.pendingCancel.resolve();
            } else if (self.dataLoading || self.pendingCancel) {
                $log.error('courseInstanceModel in unexpected state for ' +
                    'term ' + selectedTermId + ' and account ' +
                    selectedAccountId);
                errorModel.hasError = true;
                return;
            }

            // need a new Deferred object (and its promise) so we can cancel
            // this request if need be
            self.pendingCancel = $q.defer();
            var url = djangoUrl.reverse(
                'canvas_site_creator:api_course_instance_summary',
                [selectedTermId, selectedAccountId]);
            self.dataLoading = true;
            // The timeout param is used to abort the AJAX request if needed
            $http.get(url, {timeout: self.pendingCancel.promise}).success(
                    function (data, status, headers, config) {
                // reset both dataLoading (for the UI) and the pendingCancel
                // (so we can be confident about not being in an unexpected
                // state the next time the user requests course instance
                // summary info)
                self.pendingCancel = null;
                self.dataLoading = false;
                self.dataLoaded = true;
                self.totalCourses = data.recordsTotal;
                self.totalCoursesWithCanvasSite = data.recordsTotalWithCanvasSite;
                self.totalCoursesWithCanvasSiteWithExternal = data.recordsTotalWithCanvasSiteWithExternal;
                self.totalCoursesWithoutCanvasSite = data.recordsTotalWithoutCanvasSite;
                self.totalCoursesWithoutCanvasSiteWithExternal = data.recordsTotalWithoutCanvasSiteWithExternal;
                self.totalCoursesWithoutCanvasSiteAndSyncToCanvasFalse = data.recordsTotalWithoutCanvasSiteAndSyncToCanvasFalse;
                self.totalCoursesWithoutCanvasSiteAndSyncToCanvasFalseWithExternal = data.recordsTotalWithoutCanvasSiteAndSyncToCanvasFalseWithExternal;
            }).error(function (data, status, headers, config) {
                // status == 0 indicates that the request was cancelled,
                // which means that (a) the user navigated away from the
                // page before an AJAX request had a chance to return with a
                // response, or (b) we manually canceled it because it was
                // superseded by a more recent request; in any case, ignore
                // this error condition
                if (status != 0) {
                    self.dataLoading = false;
                    errorModel.hasError = true;
                }
            });
        };

        return self;
    }]);
})();
