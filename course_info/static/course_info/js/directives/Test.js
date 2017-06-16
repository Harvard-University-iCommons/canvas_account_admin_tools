(function() {
    angular.module('CourseInfo')
        .directive('test', function (){
            return {
               restrict : 'E',
               templateUrl: 'partials/test.html'
            }
        });

});

