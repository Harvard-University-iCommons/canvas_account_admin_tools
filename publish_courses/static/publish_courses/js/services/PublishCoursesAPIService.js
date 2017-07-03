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
      jobs: {
        url: getUrl('api_jobs'), pending: {}},
        courseSummary: {url: getUrl('api_show_summary'), pending: {}},
        courseList: {url: getUrl('api_course_list'), pending: {}
      }
    };

    // Returns a list of courses and their details for the given term.
    var getCourseList = function(accountId, termId) {
      var config = {
        params: {
          account_id: accountId,
          term_id: termId
        },
        logError: {enabled: true, detail: 'fetch course information'},
        pendingRequestTag: 'courseList'
      };
      return $http.get(resources.courseList.url, config
      ).then(function gotCourseList(response) {
        return JSON.parse(response.data);
      });
    };

    // Returns a summary of courses in the given term.
    // ie: There are 19 courses in this term; 18 published, 1 unpublished , 0 concluded.
    var getCourseSummary = function(accountId, termId) {
      var config = {
        params: {
          account_id: accountId,
          term_id: termId
        },
        logError: {enabled: true, detail: 'fetch course summary information'},
        pendingRequestTag: 'courses'
      };
      return $http.get(resources.courseSummary.url, config
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
      CourseList: {get: getCourseList},
      CourseSummary: {get: getCourseSummary},
      Jobs: {create: createJob},
    };
  }
})();
