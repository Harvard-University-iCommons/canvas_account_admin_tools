(function(){
    var app = angular.module('app', ['ngResource', 'ngSanitize', 'courseInstanceService']).config(function($httpProvider){
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
                    // Use for direct access to local (sslserver) rest api
                    // * remove if using passthrough
                    //config.headers = config.headers || {};
                    //config.headers.Authorization = 'Token temporarylongstringpleasefixme';
                    return config;
                }
            };
        });
    });
})();
