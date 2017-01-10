(function() {
  // todo: move append_resource_link_id() out of django_auth_lti (or this interceptor into it)
  // todo: move append_resource_link_id() out of window.globals context
  var configModule = angular.module('resourceLinkConfigModule', []);
  var resourceLinkConfig = function($httpProvider) {
    $httpProvider.interceptors.push('resourceLinkInterceptor');
  };
  var resourceLinkInterceptor = function() {
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
  configModule.config(resourceLinkConfig);
  configModule.factory('resourceLinkInterceptor', resourceLinkInterceptor);
})();
