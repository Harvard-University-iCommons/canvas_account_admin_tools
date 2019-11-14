(function() {
  var module = angular.module('PublishCoursesAPIModule', []);
  module.factory('pcapi', ['djangoUrl', '$http',
                            PublishCoursesAPIServiceFactory]);
  function PublishCoursesAPIServiceFactory(djangoUrl, $http) {
    var djangoApp = 'publish_courses:';
    var getUrl = function(resource) {
      return djangoUrl.reverse(djangoApp + ":" + resource);
    };

    var resources = {
        jobs: {url: getUrl('api_jobs'), pending: {}},
        courseList: {url: getUrl('api_course_list'), pending: {}
      }
    };

    // Returns a list of canvas courses and a summary for the given term.
    var getCourseList = function(accountId, termId) {
      var config = {
        params: {
          account_id: accountId,
          term_id: termId
        },
        logError: {enabled: true, detail: 'fetch course information'},
        pendingRequestTag: 'courseList'
      };
      console.info('INFO!!');
      console.info(resources.courseList.url);
      return $http.get(resources.courseList.url, config
      ).then(function gotCourseList(response) {
        return response.data;
      });
    };

    var createJob = function(accountId, termId, selectedCourses) {
      var params = {
        account: accountId,
        term: termId,
        course_list: selectedCourses
      };
      return $http.post(resources.jobs.url, params,
        {logError: {enabled: true, detail: 'create publish courses job'}});
    };

    return {
      CourseList: {get: getCourseList},
      Jobs: {create: createJob}
    };
  }
})();
