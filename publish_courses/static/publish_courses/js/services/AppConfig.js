(function() {
  var app = angular.module('PublishCourses');
  app.factory('AppConfig', ['DjangoContextData', appConfigFactory]);
  function appConfigFactory(DjangoContextData) {
    // todo: if we need more app config, we can extend it with DjangoContextData
    return DjangoContextData;
  }
})();
