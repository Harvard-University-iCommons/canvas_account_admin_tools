(function() {
  var module = angular.module('ActRestAPIModule', []);
  module.factory('actrapi', ['djangoUrl', '$http', '$log', '$q', 'angularDRF',
                            ActRestAPIServiceFactory]);
  function ActRestAPIServiceFactory(djangoUrl, $http, $log, $q, angularDRF) {
    var config = {baseUrl: 'api/course/v2/'};
    var api = {
      config: config,
      Schools: {url: 'schools', pending: {}, defaultConfig: {}},
      Terms: {url: 'terms', pending: {}, defaultConfig: {
        params: {
          active: 1,
          ordering: '-end_date,term_code__sort_order',
          with_end_date: 'True',
          with_start_date: 'True'
        }
      }}
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
                 + ' with params ' + angular.toJson(response.config)
                 +'. (Reason given: ' +
                 (response.statusText || 'none') + ')');
      return $q.reject(response.statusText);
    };

    var resourceUrl = function(resourceName) {
      return api.config.baseUrl + resourceName + '/';
    };

    var getConfig = function(resource, customConfig, useDefaults) {
      useDefaults = (useDefaults != null) ? useDefaults : true;
      var configDefaults = useDefaults ? api[resource].defaultConfig : {};
      return angular.merge({}, configDefaults, customConfig);
    };

    api.Schools.get = function(id, cancelActiveRequestsTag, customConfig, useDefaults) {
      var config = getConfig('Schools', customConfig, useDefaults);
      var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                  [resourceUrl(api.Schools.url) + id + '/']);
      if (cancelActiveRequestsTag) {
        cancelAnyPending('Schools', config, cancelActiveRequestsTag);
      }
      return $http.get(url, config).then(function(response) {
        if (cancelActiveRequestsTag) {
          resolvePending('Schools', cancelActiveRequestsTag);
        }
        return response.data;
      }, function errorCallback(response) {
          if (response.status == -1) {
            // request was cancelled by the timeout
            // return never-resolving promise, otherwise calling function
            // will resolve with an undefined response
            return $q.defer().promise;
          }
          return logError(response, 'get school information')
      });
    };

    api.Terms.getList = function(customConfig, useDefaults) {
      var config = getConfig('Terms', customConfig, useDefaults);
      var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                  [resourceUrl(api.Terms.url)]);
      return angularDRF.get(url, config)
        .catch(function errorCallback(response) {
          return logError(response, 'fetch terms');
        });
    };

    return api;
  }
})();
