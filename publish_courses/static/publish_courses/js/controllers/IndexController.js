(function(){
    /**
     * Angular controller for the publish courses page.
     */
    var app = angular.module('PublishCourses');
    app.controller('IndexController', IndexController);

    function IndexController($scope, $http, $timeout, $document, $window,
                            $compile, djangoUrl, $log, $q, $uibModal) {
        $scope.datatableInteractiveElementTabIndexes = [];
        // expected $scope.message format:
        //   {alertType: 'bootstrap alert class', text: 'actual message'}
        $scope.message = null;
        $scope.operationInProgress = false;
        $scope.queryString = '';
        $scope.rawFormInput = {primary: '', secondary: ''};
        // todo: move this into shared component
        $scope.school = {id: $window.school};

        $scope.filterOptions = {
                // `key` and `value` are the GET params sent to the server when
                // the option is chosen. `value` must be unique in its option list,
                // as it is also used for the HTML input element value. `value` can
                // be arbitrarily set to something unique if there are duplicate
                // values; in that case, an optional `query_value` attribute can be
                // included in the option object to indicate what to send to the
                // server. `query` is `true` if this option should trigger a GET
                // param included in the request, or `false` if it is e.g. the
                // default and should not be appended to the request params.

                terms: [
                  // todo: move a 'no terms found' into the template, remove this
                    {key:'term', value: '', name:'', query: false, text: 'Choose a term <span class="caret"></span>'}
                    // specific terms are filled out dynamically below
                ],

            };

        var schoolUrl = '/icommons_rest_api/api/course/v2/schools/'
            + $scope.school.id + '/';
        $http.get(schoolUrl)
            .then(function successCallback(response) {
                $scope.school.name = response.data.title_short || response.data.title_long;
            }, $scope.handleAjaxErrorResponse);

        // fetch active, complete terms for last five years; note this does not
        // include Ongoing term (year==1900)
        var currentYear = new Date().getFullYear();
        var httpGetConfig = {params: {
            active: 1,
            calendar_year__gte: currentYear-4,  // last five years
            limit: 100,
            ordering: '-end_date,term_code__sort_order',
            school: $scope.school.id,
            with_end_date: 'True',
            with_start_date: 'True',
        }};

        // todo: move this into shared component
        $http.get('/icommons_rest_api/api/course/v2/terms/', httpGetConfig)
            .then(function successCallback(response) {
                var dropdownSuffix = ' <span class="caret"></span>';
                $scope.filterOptions.terms =
                    $scope.filterOptions.terms.concat(
                        response.data.results.map(function (t) {
                            return {
                                key: 'term',
                                name: t.display_name,  // todo: do we need this?
                                query: true,
                                text: t.display_name + dropdownSuffix,  // todo: move into selectTerm()?
                                value: t.meta_term_id }; }));
                // todo: implement fetch-until-exhausted
                if (response.data.next && response.data.next !== '') {
                    // API returns next=null if there are no more pages
                    $log.warn('Warning: Some terms missing from dropdown!');
                }
                $scope.filters = {
                // default to first in list on load
                terms: $scope.filterOptions.terms[0],

                };
            }, $scope.handleAjaxErrorResponse);

        // todo: move this into directive
        $scope.selectTerm = function (selectedTermIndex) {
            $scope.filters.terms = $scope.filterOptions.terms[selectedTermIndex];
        };

        // todo: move this into shared library component
        $scope.handleAjaxError = function (data, status, headers, config, statusText) {
            $log.error('Error attempting to ' + config.method + ' ' + config.url +
                ': ' + status + ' ' + statusText + ': ' + JSON.stringify(data));
        };
        $scope.handleAjaxErrorResponse = function (r) {
            // angular promise then() function returns a response object,
            // unpack for our old-style error handler
            $scope.handleAjaxError(
                r.data, r.status, r.headers, r.config, r.statusText);
        };

        // todo: move this into a resource component
        $scope.publish = function() {
            // todo: button enable/disable (disable if this account-term is queued by anyone)
            // todo: response message for user (e.g. process in audit log table)
            $log.debug($scope.filters);
            $http.post('/publish_courses/api/publish', {
                account: $scope.school.id,
                term: $scope.filters.terms.value
            }).then(function logPublishResponse(response) {
                // todo: show a message
                $log.debug(response);
                $log.debug(response.data);
            }).catch($scope.handleAjaxErrorResponse);
        };
    }
})();
