(function() {
  var module = angular.module('resourceLinkModule', []);
  var resourceLinkInterceptor = function(DjangoContextData) {
    return {
      'request': function (config) {
        // Append LTI resource link ID to all AJAX requests not
        // triggered by ui-bootstrap.  Those will be served from
        // the template cache, but only if we don't screw with the
        // url.
        //
        // window.globals.append_resource_link_id function added by
        // django_auth_lti/js/resource_link_id.js
        if (!config.url.startsWith('uib/template/')) {
          config.url = window.globals.append_resource_link_id(config.url);
        }
        return config;
      }
    };
  };
  module.factory('resourceLinkInterceptor', ['DjangoContextData',
    resourceLinkInterceptor]);
  module.config(['$httpProvider', function($httpProvider) {
    $httpProvider.interceptors.push('resourceLinkInterceptor');
  }]);
})();
