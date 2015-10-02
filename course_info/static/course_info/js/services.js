var courseInstanceService = angular.module('courseInstanceService', ['ngResource']);

courseInstanceService.factory('CourseInstance', ['$resource', function ($resource) {
    return $resource('https://localhost:8000/icommons_rest_api/api/course/v2/course_instances/:id',
        {id: '@id', format: 'json'},
        // API delivers array of resources in the 'results' key of the json,
        // so the collection doesn't actual return an Array at its root
        {'query': {method: 'GET', isArray: false}}
    );
}]);