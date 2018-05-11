(function(){
    var app = angular.module('PublishCourses',
      ['resourceLinkModule',       // append resource link IDs
       'djangoAJAXConfigModule',   // CSRF compatibility with DRF
       'angularDRFModule',         // DRF-specific services like fetch all
       'ActRestAPIModule',         // Act (icommons) REST API helpers
       'pendingHandlerModule',     // cancels pending requests
       'LogErrorHandlerModule',    // logs AJAX errors to console consistently
       'PublishCoursesAPIModule',  // Django publish_courses app API helpers
       'TermDropdownDirective',    // Reusable Term Dropdown
       'djng.urls',
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
