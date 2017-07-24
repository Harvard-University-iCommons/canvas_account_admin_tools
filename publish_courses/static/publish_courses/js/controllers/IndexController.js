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

        $scope.addSelectedCourse = function(courseData){
            $scope.selectedCourses[courseData['id']] = courseData;
        };

        $scope.removeSelectedCourse = function(courseData){
            delete $scope.selectedCourses[courseData['id']];
        };

        $scope.getSelectedCourseIdsCount = function(){
            return Object.keys($scope.selectedCourses).length;
        };

        $scope.getSelectedCourses = function(){
            return Object.keys($scope.selectedCourses).map(function(key){
                return $scope.selectedCourses[key]['id'];
            })
        };

        $scope.getPublishButtonMessage = function(){
            return $scope.getSelectedCourseIdsCount() ? 'Selected' : 'All';
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
                    $scope.addSelectedCourse($scope.dataTable.row(index).data());
                } else {
                    $scope.removeSelectedCourse($scope.dataTable.row(index).data());
                }
            });
        };

        $scope.syncSelectionCheckboxes = function(){
            $('#courseInfoDT tbody .col-select').each(function(o) {
                var $checkbox = $(this);
                var courseId = $checkbox.data('id');
                var isSelected = Boolean($scope.selectedCourses[courseId]);
                $checkbox.closest('tr').toggleClass('selected', isSelected);
                $checkbox.prop('checked', isSelected);
            });
            $scope.selectAll = !$('#courseInfoDT tbody tr').not('.selected').length;
        };

        $scope.$watch('selectedCourses', $scope.syncSelectionCheckboxes, true);

        $scope.handleRowClick = function(e){
            var $tr = $(e.target).closest('tr');
            var selected = !$tr.hasClass('selected');
            var courseData = $scope.dataTable.row($tr).data();
            if (selected) {
                $scope.addSelectedCourse(courseData);
            } else {
                $scope.removeSelectedCourse(courseData);
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

        $scope.loadCoursesSummary = function(data){
            $scope.coursesSummary = data;
        };

        $scope.publish = function() {
            $scope.clearMessages();
            var accountId = $scope.school.id;
            var termId = $scope.selectedTerm.meta_term_id;
            var selectedCourses = null;
            // disable Publish button (until user changes term)
            $scope.operationInProgress = true;

            // If any courses have been selected, then set the selectedCourses var to the list of selected course id's
            // so that only those courses are published.
            // If none have been selected, then null will be sent and all unpublished courses in the given
            // account and term will be published.
            if ($scope.getSelectedCourseIdsCount() > 0) {
                selectedCourses = $scope.getSelectedCourses();
            }

            pcapi.Jobs.create(accountId, termId, selectedCourses
                ).then(function publishSucceeded(response) {
                    $scope.message = $scope.messages.success;
                    $log.debug(response);
                    $log.debug(response.data);
                }, function publishFailed(response) {
                    $scope.message = $scope.messages.failure;
                }).finally(function cleanUpAfterPublish() {
                    $scope.operationInProgress = false;
                });

            $scope.showDataTable = false;
        };

        $scope.publishButtonDisabled = function() {
            // disable button when:
            // - nothing is selected in the term dropdown
            // - there are no publishable sites in the term
            // - submitting a job
            // - user has successfully submitted a job
            return !$scope.selectedTerm
                   || $scope.coursesSummary.unpublished == 0
                   || $scope.operationInProgress
                   || ($scope.message && ($scope.message == $scope.messages.success));
        };

        $scope.termSelected = function(selectedTerm) {
            $scope.selectedTerm = selectedTerm;
            $scope.clearMessages();
            $scope.loadCourseData();
            // Reset any selected courses when changing term
            $scope.selectedCourses = {};
        };

        $scope.initialize();

        // Makes the call to get all courses information for the selected term and account and display that information
        // as both a summary and a data table.
        $scope.loadCourseData = function() {
            // If the data table already exists, hide and clear the table while the new data is loaded.
            if ($scope.dataTable) {
                $scope.showDataTable = false;
                $scope.dataTable.destroy();
            }
            var accountId = $scope.school.id;
            var termId = $scope.selectedTerm.meta_term_id;
            $scope.operationInProgress = true;
            $scope.loadingSummary = true;
            pcapi.CourseList.get(accountId, termId).then(function (data) {
                $scope.loadCoursesSummary(data['course_summary']);
                var canvasURL = data['canvas_url'];
                $scope.dataTable = $('#courseInfoDT').DataTable({
                    retrieve: true,
                    dom: '<lf<rt>ip>',
                    language: {
                        info: 'Showing _START_ to _END_ of _TOTAL_ course sites',
                        emptyTable: 'There are no course sites to display.',
                        lengthMenu: 'Show _MENU_ course sites',
                        search: 'Search by Course Title, Canvas ID, Course Code or SIS ID'
                    },
                    data: data['courses'],
                    order: [[1, 'asc']],
                    columns: [
                        {
                            data: 'id',
                            orderable: false,
                            width: '5%',
                            className: 'col-align-center',
                            render: $scope.renderSelectionColumn},
                        {data: 'name'},
                        {
                            data: 'id',
                            width: '15%',
                            render: function(data, type, row, meta) {
                                return '<a target="_blank" href="' + canvasURL + '/courses/' + row.id + '">' + data + '</a>';
                            }
                        },
                        {data: 'course_code', width: '15%'},
                        {data: 'sis_course_id', width: '15%'}

                    ],
                    preDrawCallback: function(){
                        $('#courseInfoDT tbody tr').off('click', $scope.handleRowClick);
                    },
                    drawCallback: function(){
                        $scope.syncSelectionCheckboxes();
                        $('#courseInfoDT tbody tr').on('click', $scope.handleRowClick);
                        $scope.showDataTable = true;
                        $scope.loadingSummary = false;
                        $scope.operationInProgress = false;
                    }
                });
            });
        };
    }
})();
