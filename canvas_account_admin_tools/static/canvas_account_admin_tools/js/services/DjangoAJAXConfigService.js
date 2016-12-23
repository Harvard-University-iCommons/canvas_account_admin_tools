(function() {
  var configModule = angular.module('djangoAJAXConfigModule', []);
  configModule.config(['$httpProvider', djangoAJAXConfigFactory]);
  function djangoAJAXConfigFactory($httpProvider) {
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
}})();
