(function(){
    /**
     * Angular controller for the publish courses page.
     */
    var app = angular.module('PublishCourses');
    app.controller('IndexController', IndexController);

    function IndexController($scope, $log, actrapi, AppConfig, pcapi) {
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
        $scope.showDataTable = false;
        // Canvas course id's that have been selected in the data table
        $scope.selectedCourses = {};
        $scope.selectAll = false;

        $scope.addSelectedCourseInstance = function(courseInstanceData){
            $scope.selectedCourses[courseInstanceData['id']] = courseInstanceData;
        };

        $scope.removeSelectedCourseInstance = function(courseInstanceData){
            delete $scope.selectedCourses[courseInstanceData['id']];
        };

        $scope.getSelectedCourseIdsCount = function(){
            return Object.keys($scope.selectedCourses).length;
        };

        $scope.getSelectedCourses = function(){
            return Object.keys($scope.selectedCourses).map(function(key){
                return $scope.selectedCourses[key]['id'];
            })
        };

        // Return a checkbox used in the first column of the data table, with the course id as its value.
        $scope.renderSelectionColumn = function(data, type, row, meta){
            return '<input type="checkbox" class="col-select" data-id="' + data + '"/>';
        };

        $scope.toggleSelectAll = function(){
            $scope.selectAll = !$scope.selectAll;
            $('#courseInfoDT tbody tr').each(function(index, tr){
                var $checkbox = $(tr).find('.col-select');
                $checkbox.prop('checked', $scope.selectAll);
                if ($scope.selectAll) {
                    $scope.addSelectedCourseInstance($scope.dataTable.row(index).data());
                } else {
                    $scope.removeSelectedCourseInstance($scope.dataTable.row(index).data());
                }
            });
        };

        $scope.handleRowClick = function(e){
            var $tr = $(e.target).closest('tr');
            var selected = !$tr.hasClass('selected');
            var courseInstanceData = $scope.dataTable.row($tr).data();
            if (selected) {
                $scope.addSelectedCourseInstance(courseInstanceData);
            } else {
                $scope.removeSelectedCourseInstance(courseInstanceData);
            }
            $scope.$apply();
        };

        $scope.filterOutOngoingTerms = function(term) {
          return term.term_code != 99;  // ongoing term
        };
        $scope.filterOutConcludedTerms = function(term) {
            var comparisonDate = new Date(term.conclude_date || term.end_date);
            return comparisonDate >= $scope.currentDate;
        };
        $scope.initialize = function() {
            // get school display name from the sis_account_id context
            actrapi.Schools.get($scope.school.id)
                .then(function gotSchool(r) {
                    $scope.school.name = r.title_short
                                         || r.title_long
                                         || $scope.school.id;});

            // fetch active, un-concluded terms
            var options = {config: {params: {school: $scope.school.id}}};
            actrapi.Terms.getList(options)
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
            pcapi.Jobs.createAll(accountId, termId
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
            // disable button when:
            // - nothing is selected in the term dropdown
            // - there are no publishable sites in the term
            // - submitting a job
            // - user has successfully submitted a job

            // todo This is commented out to prevent creation of jobs prior to the UI development story TLT-3144
            //
            // return !$scope.selectedTerm
            //        || $scope.coursesSummary.unpublished == 0
            //        || $scope.operationInProgress
            //        || ($scope.message && ($scope.message == $scope.messages.success));
            return true;
        };

        $scope.publishSelected = function() {
            $scope.clearMessages();
            var accountId = $scope.school.id;
            var termId = $scope.selectedTerm.meta_term_id;
            // disable Publish button (until user changes term)
            $scope.operationInProgress = true;
            pcapi.Jobs.createSelected(accountId, termId, $scope.getSelectedCourses()
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

        $scope.termSelected = function(selectedTerm) {
            $scope.selectedTerm = selectedTerm;
            $scope.clearMessages();
            $scope.loadCoursesSummary();
            $scope.updateDataTable();
        };

        $scope.initialize();

        $scope.updateDataTable = function() {
            $scope.showDataTable = true;
            if ($scope.dataTable) {
                $scope.dataTable.destroy();
            }
            var accountId = $scope.school.id;
            var termId = $scope.selectedTerm.meta_term_id;
            pcapi.CourseList.get(accountId, termId).then(function (data) {
                $scope.dataTable = $('#courseInfoDT').DataTable({
                    retrieve: true,
                    dom: '<lf<rt>ip>',
                    language: {
                        info: 'Showing _START_ to _END_ of _TOTAL_ courses',
                        emptyTable: 'There are no courses to display.'
                    },
                    data: data,
                    order: [[3, 'asc']],
                    columns: [
                        {
                            data: 'id',
                            orderable: false,
                            width: '5%',
                            className: 'col-align-center',
                            render: $scope.renderSelectionColumn},
                        {data: 'id'},
                        {data: 'course_code'},
                        {data: 'name'},
                        {data: 'sis_course_id'},
                        {data: 'workflow_state'}
                    ],
                    preDrawCallback: function(){
                        $('#courseInfoDT tbody tr').off('click', $scope.handleRowClick);
                    },
                    drawCallback: function(){
                        $('#courseInfoDT tbody tr').on('click', $scope.handleRowClick);
                    }
                });
            });
        };
    }
})();
