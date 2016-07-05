(function(){
    var app = angular.module('PeopleTool',
                             ['ngSanitize', 'ng.django.urls', 'ngRoute',
                              'ui.bootstrap', 'datatables']);

    app.config(['$httpProvider', '$routeProvider',
                function($httpProvider, $routeProvider){
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
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
                templateUrl: 'partials/search.html',
                controller: 'SearchController',
            })
            .otherwise({
                redirectTo: '/',
            });
    }]);
})();
