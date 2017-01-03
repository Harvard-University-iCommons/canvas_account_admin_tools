// todo: move into angular-drf.js?
(function() {
  var angularDRFModule = angular.module('angularDRFModule', []);
  angularDRFModule.factory('angularDRF', ['$http', '$q', angularDRF]);
})();
