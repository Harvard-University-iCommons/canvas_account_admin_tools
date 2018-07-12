(function () {
    var app = angular.module('app',
                  ['djng.urls', 'ngSanitize', 'ui.bootstrap']);

    app.config(function ($httpProvider) {
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        $httpProvider.interceptors.push(function () {
            return {
                'request': function (config) {
                    // Append LTI resource link ID to all AJAX requests
                    // window.globals.append_resource_link_id function added by
                    // django_auth_lti/js/resource_link_id.js
                    if (!(config.url.startsWith('template/alert/') ||
                                config.url.startsWith('template/modal/'))) {
                        config.url = window.globals.append_resource_link_id(config.url);
                    }
                    return config;
                }
            };
        });
    });
})();
