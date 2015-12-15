(function() {
    // stores details on the course instances currently visible in the search
    // view.  used to share that data with the enrollments view.
    var app = angular.module('CourseInfo');

    app.factory('courseInstances', function() {
        return {
            instances: {}
        };
    });


    app.factory('restService', '$http', function($http) {
        var baseUrl = '/icommons_rest_api/api';
        return {
            addUser: function (user) {
                console.log(user);
                var apiCall = '/course_instance/' + user.course_instance_id + '/people';
                return $http.post(baseUrl + apiCall, user);
            }
        }
    });

})();
