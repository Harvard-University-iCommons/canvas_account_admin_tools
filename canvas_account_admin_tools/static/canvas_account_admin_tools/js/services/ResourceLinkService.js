(function() {
  var module = angular.module('resourceLinkModule', []);
  var resourceLinkInterceptor = function(DjangoContextData) {
    var appendResourceLinkId = function(url){
      if (!url.match(/resource_link_id/)) {
        var url_separator = (url.match(/\?/)) ? '&' : '?';
        return url + url_separator + 'resource_link_id='
          + DjangoContextData.resource_link_id;
      }
      return url;
    };
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
          config.url = appendResourceLinkId(config.url);
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
