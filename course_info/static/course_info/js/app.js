(function(){
    var app = angular.module('CourseInfo',
                             ['ngSanitize', 'ng.django.urls', 'ngRoute', 'datatables']);
    
    app.config(['$httpProvider', '$routeProvider',
                function($httpProvider, $routeProvider){
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        $httpProvider.interceptors.push(function(){
            return {
                'request': function(config){
                    // Append LTI resource link ID to all AJAX requests
                    // window.globals.append_resource_link_id function added by
                    // django_auth_lti/js/resource_link_id.js
                    config.url = window.globals.append_resource_link_id(config.url);
                    return config;
                }
            };
        });

        $routeProvider
            .when('/', {
                templateUrl: 'partials/search.html',
                controller: 'SearchController',
            })
            .when('/people/:course_instance_id', {
                templateUrl: 'partials/people.html',
                controller: 'PeopleController',
            })
            .otherwise({
                redirectTo: '/',
            });
    }]);
})();
