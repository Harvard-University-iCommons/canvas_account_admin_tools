(function() {
  var module = angular.module('PublishCoursesAPIModule', []);
  module.factory('pcapi', ['djangoUrl', '$http', '$log', '$q',
                            PublishCoursesAPIServiceFactory]);
  function PublishCoursesAPIServiceFactory(djangoUrl, $http, $log, $q) {
    // todo: refactor pending request resolution (see ATRAPIService)
    var djangoApp = 'publish_courses:';
    var getUrl = function(resource) {
      return djangoUrl.reverse(djangoApp + resource);
    };

    var api = {
      jobs: {url: getUrl('api_jobs'), pending: {}},
      courses: {url: getUrl('api_show_summary'), pending: {}}
    };

        // todo: implement as an http interceptor
    var cancelAnyPending = function(resourceName, config, pendingRequestTag) {
      pendingRequestTag = pendingRequestTag || 'default';
      if (api[resourceName].pending[pendingRequestTag]) {
        // data still loading from previous request, cancel it
        api[resourceName].pending[pendingRequestTag].resolve();
        $log.debug('cancelling pending "' + pendingRequestTag + '" request '
                   + 'for resource ' + resourceName);
      }
      // need new Deferred object (and its promise) to cancel request if need be
      api[resourceName].pending[pendingRequestTag] = $q.defer();
      config.timeout = api[resourceName].pending[pendingRequestTag].promise;
      $log.debug('updated config: ' + angular.toJson(config));
    };

    var resolvePending = function(resourceName, pendingRequestTag) {
      pendingRequestTag = pendingRequestTag || 'default';
      api[resourceName].pending[pendingRequestTag] = null;
      $log.debug('resolving pending "' + pendingRequestTag + '" request '
                 + 'for resource ' + resourceName);
    };

    // todo: implement as an http interceptor
    var handleAjaxError = function (response, data, status, headers, config,
                                    statusText) {
      var method = (config||{}).method;
      var url = (config||{}).url;
      if (method && url && data && status && statusText) {
        $log.error('Error attempting to ' + method + ' ' + url +
          ': ' + status + ' ' + statusText + ': ' + JSON.stringify(data));
      } else {
        $log.error('Unknown ajax error: ' + response);
      }
    };

    var handleAjaxErrorResponse = function (r) {
      // angular promise then() function returns a response object,
      // unpack for old-style error() handler
      handleAjaxError(r, r.data, r.status, r.headers, r.config, r.statusText);
    };

    var logResponseError = function(response, operationText) {
      handleAjaxErrorResponse(response);
      $log.error('Unable to ' + operationText || 'perform operation'
                 + ' with params ' + angular.toJson(response.config)
                 +'. (Reason given: ' +
                 (response.statusText || 'none') + ')');
      return $q.reject(response.statusText);
    };

    // todo: cache responses?
    var getCourseSummary = function(accountId, termId) {
      var config = {params: {
        account_id: accountId,
        term_id: termId
      }};
      cancelAnyPending('courses', config);
      return $http.get(api.courses.url, config
      ).then(function gotCourseSummary(response) {
        resolvePending('courses');
        return response.data;
      }).catch(function errorCallback(response) {
          if (response.status == -1) {
            // request was cancelled by the timeout
            // return never-resolving promise, otherwise calling function
            // will resolve with an undefined response
            return $q.defer().promise;
          }
          return logResponseError(response, 'fetch school');
      });
    };

    var createJob = function(accountId, termId) {
      var params = {
        account: accountId,
        term: termId
      };
      return $http.post(api.jobs.url, params)
      .catch(function errorCallback(response) {
        return logResponseError(response, 'create publish courses');
      });
    };

    var resourcesAPI = {
      CourseSummary: {get: getCourseSummary},
      Jobs: {create: createJob}
    };

    return resourcesAPI;
  }
})();
