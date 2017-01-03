(function(){
    /**
     * Angular controller for the publish courses page.
     */
    var app = angular.module('PublishCourses');
    app.controller('IndexController', IndexController);

    function IndexController($scope, $log, atrapi, AppConfig, pcapi) {
        // expected $scope.message format:
        //   {alertType: 'bootstrap alert class', text: 'actual message'}
        $scope.message = null;
        $scope.operationInProgress = false;
        $scope.currentDate = new Date();
        $scope.school = {id: AppConfig.school};
        $scope.selectedTerm = null;
        $scope.terms = null;
        $scope.coursesSummary = {};
        $scope.loadingSummary = false;
        $scope.messages = {
            success: {
                alertType: 'success',
                text: 'These courses will be published momentarily. ' +
                'Please check the summary on this page, or the reports ' +
                'in your account settings, to verify that all courses ' +
                'are published.'},
            failure: {
                alertType: 'danger',
                text: 'There was a problem publishing these courses.'} };

        $scope.filterOutOngoingTerms = function(term) {
          return term.term_code != 99;  // ongoing term
        };
        $scope.filterOutConcludedTerms = function(term) {
            var comparisonDate = new Date(term.conclude_date || term.end_date);
            return comparisonDate >= $scope.currentDate;
        };
        $scope.initialize = function() {
            // get school display name from the sis_account_id context
            atrapi.Schools.get($scope.school.id)
                .then(function gotSchool(r) {
                    $scope.school.name = r.title_short
                                         || r.title_long
                                         || $scope.school.id;});

            // fetch active, un-concluded terms
            var termsGetConfig = {params: {school: $scope.school.id}};
            atrapi.Terms.getList(termsGetConfig)
                .then(function gotTerms(terms) {
                    var currentTerms = terms.filter($scope.filterOutConcludedTerms);
                    $scope.terms = currentTerms.filter($scope.filterOutOngoingTerms);
                });
        };
        $scope.clearMessages = function () {
            $scope.message = null;
        };
        $scope.loadCoursesSummary = function(){
            $scope.loadingSummary = true;
            var accountId = $scope.school.id;
            var termId = $scope.selectedTerm.meta_term_id;
            pcapi.CourseSummary.get(accountId, termId).then(function (data) {
                $scope.coursesSummary = data;
                $scope.loadingSummary = false;
            });
        };
        $scope.publish = function() {
            $scope.clearMessages();
            var accountId = $scope.school.id;
            var termId = $scope.selectedTerm.meta_term_id;
            // disable Publish button (until user changes term)
            $scope.operationInProgress = true;
            pcapi.Jobs.create(accountId, termId
            ).then(function publishSucceeded(response) {
                $scope.message = $scope.messages.success;
                $log.debug(response);
                $log.debug(response.data);
            }, function publishFailed(response) {
                $scope.message = $scope.messages.failure;
            }).finally(function cleanUpAfterPublish() {
                $scope.operationInProgress = false;
            });
        };
        $scope.publishButtonDisabled = function() {
            return ($scope.operationInProgress
                    || !$scope.selectedTerm
                    || $scope.coursesSummary.unpublished == 0);
        };
        $scope.termSelected = function(selectedTerm) {
            $scope.selectedTerm = selectedTerm;
            $scope.clearMessages();
            $scope.loadCoursesSummary();
        };

        $scope.initialize();
    }
})();
