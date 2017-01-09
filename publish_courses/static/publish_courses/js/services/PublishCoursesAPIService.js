(function() {
  var module = angular.module('PublishCoursesAPIModule', []);
  module.factory('pcapi', ['djangoUrl', '$http', '$log', '$q',
                            PublishCoursesAPIServiceFactory]);
  function PublishCoursesAPIServiceFactory(djangoUrl, $http, $log, $q) {
    // todo: common library for error handling
    // todo: refactor pending request resolution (see ATRAPIService)
    var djangoApp = 'publish_courses:';
    var getUrl = function(resource) {
      return djangoUrl.reverse(djangoApp + resource);
    };

    var resources = {
      jobs: {url: getUrl('api_jobs'), pending: null},
      courses: {url: getUrl('api_show_summary'), pending: null}
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
      if (resources.courses.pending) {
        // data still loading from previous request, cancel it
        resources.courses.pending.resolve();
      }
      // need new Deferred object (and its promise) to cancel request if need be
      resources.courses.pending = $q.defer();
      var config = {params: {
        account_id: accountId,
        term_id: termId
      }, timeout: resources.courses.pending.promise};
      return $http.get(resources.courses.url, config
      ).then(function gotCourseSummary(response) {
        resources.courses.pending = null;
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
      return $http.post(resources.jobs.url, params)
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
