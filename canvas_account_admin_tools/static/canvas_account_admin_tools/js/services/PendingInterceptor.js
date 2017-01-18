(function() {
  var module = angular.module('pendingHandlerModule', []);
  var pendingInterceptor = function($q) {
    var tags = {};
    return {
      request: function cancelAnyPending(config) {
        var tag = config.pendingRequestTag;
        if (tag) {
          if ((tags[tag]||{}).pending) {
            // data still loading from previous request, cancel it
            tags[tag].pending.resolve();
          }
          // need new Deferred (and its promise) to cancel request if need be
          tags[tag] = {pending: $q.defer()};
          config.timeout = tags[tag].pending.promise;
        }
        return config;
      },
      response: function resolvePending(response) {
        var tag = response.config.pendingRequestTag;
        if (tag) {
          if (response.status == -1) {
            return $q.defer().promise;
          }
          tags[tag] = {pending: null};
        }
        return response;
      }
    }
  };
  module.factory('pendingInterceptor', ['$q', pendingInterceptor]);
  module.config(['$httpProvider', function($httpProvider) {
      $httpProvider.interceptors.push('pendingInterceptor');
  }]);
})();
