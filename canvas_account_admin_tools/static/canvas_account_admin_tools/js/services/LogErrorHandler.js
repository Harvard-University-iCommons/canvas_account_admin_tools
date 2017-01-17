(function() {
  var module = angular.module('LogErrorHandlerModule', []);
  var logErrorHandler = function($log, $q) {
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

    var logError = function(response) {
      var logError = (response.config || {}).logError || {};
      var enabled = logError.enabled || false;

      if (!enabled) { return response }

      handleAjaxErrorResponse(response);

      var detail = logError.detail || 'perform operation';
      $log.error('Unable to ' + detail
                 + ' with config ' + angular.toJson(response.config)
                 +'. (Reason given: ' +
                 (response.statusText || 'none') + ')');

      return $q.reject(response.statusText);
    };

    return { responseError: logError };
  };
  module.factory('logErrorHandler', ['$log', '$q', logErrorHandler]);
  module.config(['$httpProvider', function($httpProvider) {
      $httpProvider.interceptors.push('logErrorHandler');
  }]);
})();
