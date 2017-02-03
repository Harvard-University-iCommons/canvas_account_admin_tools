(function() {
  var module = angular.module('PublishCoursesAPIModule', []);
  module.factory('pcapi', ['djangoUrl', '$http',
                            PublishCoursesAPIServiceFactory]);
  function PublishCoursesAPIServiceFactory(djangoUrl, $http) {
    var djangoApp = 'publish_courses:';
    var getUrl = function(resource) {
      return djangoUrl.reverse(djangoApp + resource);
    };

    var resources = {
      jobs: {url: getUrl('api_jobs'), pending: {}},
      courses: {url: getUrl('api_show_summary'), pending: {}}
    };

    var getCourseSummary = function(accountId, termId) {
      var config = {
        params: {
          account_id: accountId,
          term_id: termId
        },
        logError: {enabled: true, detail: 'fetch course summary information'},
        pendingRequestTag: 'courses'
      };
      return $http.get(resources.courses.url, config
      ).then(function gotCourseSummary(response) {
        return response.data;
      });
    };

    var createJob = function(accountId, termId) {
      var params = {
        account: accountId,
        term: termId
      };
      return $http.post(resources.jobs.url, params,
        {logError: {enabled: true, detail: 'create publish courses job'}});
    };

    return {
      CourseSummary: {get: getCourseSummary},
      Jobs: {create: createJob}
    };
  }
})();
