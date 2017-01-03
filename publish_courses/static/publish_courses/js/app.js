(function(){
    var app = angular.module('PublishCourses',
      ['resourceLinkConfigModule',  // append resource link IDs
        'djangoAJAXConfigModule',   // CSRF compatibility with DRF
        'angularDRFModule',         // DRF-specific services like fetch all
        'ATRAPIModule',             // AT (icommons) REST API helpers
        'PublishCoursesAPIModule',  // Django publish_courses app API helpers
        'TermDropdownDirective',    // Reusable Term Dropdown
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
