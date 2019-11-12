(function(){
    var app = angular.module('PublishCourses',
      ['djangoAJAXConfigModule',   // CSRF compatibility with DRF
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
    app.config(['$routeProvider', function ($httpProvider, $routeProvider){
        $httpProvider.interceptors.push(function(){
            return {
                'request': function(config){
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
        });
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
