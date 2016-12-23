(function(){
    var app = angular.module('PublishCourses',
      ['resourceLinkConfigModule',  // append resource link IDs
        'djangoAJAXConfigModule',   // CSRF compatibility with DRF
        'ng.django.urls',
        'ngRoute',
        'ngSanitize',
        'ui.bootstrap']);
    app.config(['$routeProvider', function ($routeProvider){
        $routeProvider
            .when('/', {
                templateUrl: 'partials/list.html',
                controller: 'IndexController',
            })
            .otherwise({
                redirectTo: '/',
            });
    }]);
})();
