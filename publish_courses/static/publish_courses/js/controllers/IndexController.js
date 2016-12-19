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

                schools: [
                    // specific schools are filled out dynamically below
                ],
                terms: [
                    {key:'term_code', value: 'None', name:'', query: false, text: 'Choose a term <span class="caret"></span>'}
                    // specific terms are filled out dynamically below
                ],

            };

        // todo: we actually need the year as well; it would be easiest to fetch terms from Canvas (although we might have to do that in Django instead of here)
        $http.get('/icommons_rest_api/api/course/v2/term_codes/?limit=100')
            .then(function successCallback(response) {
                $log.debug(" in here1");
                $scope.filterOptions.terms =
                    $scope.filterOptions.terms.concat(response.data.results.map(function (tc) {
                        return {
                            key: 'term_code',
                            value: tc.term_code,
                            name: tc.term_name,
                            query: true,
                            text: tc.term_name + ' <span class="caret"></span>',
                        };
                    }));
                // todo: implement fetch-until-exhausted
                if (response.data.next && response.data.next !== '') {
                    // API returns next=null if there are no more pages
                    $log.warn('Warning: Some terms missing from dropdown!');
                }
            }, function errorCallback(response) {
                $log.error(response.statusText);
            });

            Array.prototype.push.apply(
                $scope.filterOptions.schools,
                $window.schoolOptions);

            $scope.filters = {
                // default to first in list on load
                schools: $scope.filterOptions.schools[0],
                terms: $scope.filterOptions.terms[0],

            };


        $scope.clearMessages = function () {
            $scope.message = null;
        };

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
                account: $scope.filters.schools.value,
                term: $scope.filters.terms.value
            }).then(function logPublishResponse(response) {
                $log.debug(response);
                $log.debug(response.data);
            }).catch($scope.handleAjaxErrorResponse);
        }
    }
})();
