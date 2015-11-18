(function() {
    // stores details on the course instances currently visible in the search
    // view.  used to share that data with the enrollments view.
    var app = angular.module('CourseInfo');

    app.factory('courseInstances', function() {
        return {
            instances: {}
        };
    });
})();
