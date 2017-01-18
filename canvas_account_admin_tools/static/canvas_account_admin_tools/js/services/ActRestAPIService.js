(function() {
  var module = angular.module('ActRestAPIModule', []);
  module.factory('actrapi', ['djangoUrl', '$http', 'angularDRF',
                            ActRestAPIServiceFactory]);
  function ActRestAPIServiceFactory(djangoUrl, $http, angularDRF) {
    var serviceConfig = {baseUrl: 'api/course/v2/'};
    var api = {
      config: serviceConfig,
      Schools: {url: 'schools', pending: {}, defaultConfig: {
        logError: {enabled: true, detail: 'fetch school details'}
      }},
      Terms: {url: 'terms', pending: {}, defaultConfig: {
        params: {
          active: 1,
          ordering: '-end_date,term_code__sort_order',
          with_end_date: 'True',
          with_start_date: 'True'
        },
        logError: {enabled: true, detail: 'fetch active terms'}
      }}
    };

    var resourceUrl = function(resourceName) {
      return api.config.baseUrl + resourceName + '/';
    };

    var getConfig = function(resource, options) {
      var o = options || {};
      var useDefaults = (o.useDefaults !== undefined) ? Boolean(o.useDefaults) : true;
      var configDefaults = useDefaults ? api[resource].defaultConfig : {};
      return angular.merge({}, configDefaults, o.config||{});
    };

    api.Schools.get = function(id, options) {
      var config = getConfig('Schools', options);
      var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                  [resourceUrl(api.Schools.url) + id + '/']);
      return $http.get(url, config).then(function(response) {
        return response.data;
      });
    };

    api.Terms.getList = function(options) {
      var config = getConfig('Terms', options);
      var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                  [resourceUrl(api.Terms.url)]);
      return angularDRF.get(url, config);
    };

    return api;
  }
})();
