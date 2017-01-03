(function() {
  var module = angular.module('ATRAPIModule', []);
  module.factory('atrapi', ['djangoUrl', '$http', '$log', '$q', 'angularDRF',
                            ATRAPIServiceFactory]);
  function ATRAPIServiceFactory(djangoUrl, $http, $log, $q, angularDRF) {
    // todo: cache results (for configurable window of time)?
    // todo: make baseUrl and defaults configurable by application
    // todo: refactor common fetch code (e.g. defaults resolution, cancel/resolve pending)
    // todo: common library for error handling
    var baseUrl = 'api/course/v2/';
    var resources = {
      Schools: {url: baseUrl + 'schools/', pending: {}},
      Terms: {url: baseUrl + 'terms/', pending: {}}
    };

    var cancelAnyPending = function(resourceName, config, pendingRequestTag) {
      pendingRequestTag = pendingRequestTag || 'default';
      if (resources[resourceName].pending[pendingRequestTag]) {
        // data still loading from previous request, cancel it
        resources[resourceName].pending[pendingRequestTag].resolve();
        $log.debug('cancelling pending "' + pendingRequestTag + '" request '
                   + 'for resource ' + resourceName);
      }
      // need new Deferred object (and its promise) to cancel request if need be
      resources[resourceName].pending[pendingRequestTag] = $q.defer();
      config.timeout = resources[resourceName].pending[pendingRequestTag].promise;
      $log.debug('updated config: ' + angular.toJson(config));
    };

    var resolvePending = function(resourceName, pendingRequestTag) {
      pendingRequestTag = pendingRequestTag || 'default';
      resources[resourceName].pending[pendingRequestTag] = null;
      $log.debug('resolving pending "' + pendingRequestTag + '" request '
                 + 'for resource ' + resourceName);
    };

    var handleAjaxError = function (response, data, status, headers, config,
                                    statusText) {
      var method = (config||{}).method;
      var url = (config||{}).url;
      if (method && url && data && status && statusText) {
        $log.error('Error attempting to ' + method + ' ' + url +
          ': ' + status + ' ' + statusText + ': ' + JSON.stringify(data));
      } else {
        $log.error('Unknown ajax error: ' + JSON.stringify(response));
      }
    };

    var handleAjaxErrorResponse = function (r) {
      // angular promise then() function returns a response object,
      // unpack for our old-style error handler
      handleAjaxError(r, r.data, r.status, r.headers, r.config, r.statusText);
    };

    var logError = function(response, operationText) {
      handleAjaxErrorResponse(response);
      $log.error('Unable to ' + operationText || 'perform operation'
                 + ' with params ' + angular.toJson(config)
                 +'. (Reason given: ' +
                 (response.statusText || 'none') + ')');
      return $q.reject(response.statusText);
    };

    resources.Schools.get = function(id, cancelActiveRequestsTag) {
      var url = djangoUrl.reverse('icommons_rest_api_proxy', [resources.Schools.url + id + '/']);
      var getConfig = {};
      if (cancelActiveRequestsTag) {
        cancelAnyPending('Schools', getConfig, cancelActiveRequestsTag);
      }
      return $http.get(url, getConfig).then(function(response) {
        if (cancelActiveRequestsTag) {
          resolvePending('Schools', cancelActiveRequestsTag);
        }
        return response.data;
      }, function errorCallback(response) {
          // status == -1 indicates that the request was cancelled by the timeout
          if (response.status != -1) {
            return logError(response, 'get school information')
          }
      });
    };

    resources.Terms.getList = function(customConfig, useDefaults) {
      var configDefaults = {
        params: {
          active: 1,
          ordering: '-end_date,term_code__sort_order',
          with_end_date: 'True',
          with_start_date: 'True'
        }
      };
      useDefaults = (useDefaults != null) ? useDefaults : true;
      var getConfig = customConfig;  // if !useDefaults, just use the params provided
      if (useDefaults) {
        getConfig = angular.merge({}, configDefaults, customConfig);
      }
      var url = djangoUrl.reverse('icommons_rest_api_proxy', [resources.Terms.url]);
      return angularDRF.get(url, getConfig)
        .catch(function errorCallback(response) {
          return logError(response, 'fetch terms');
        });
    };

    return resources;
  }
})();
