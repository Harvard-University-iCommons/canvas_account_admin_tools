(function() {
    // Stores  details of the Person being selected in the search
    // view.  It is used to share that data with the courses view.
    var app = angular.module('PeopleTool');

    app.factory('personInfo', function() {
        return {
            details: {}
        };
    });
})();
