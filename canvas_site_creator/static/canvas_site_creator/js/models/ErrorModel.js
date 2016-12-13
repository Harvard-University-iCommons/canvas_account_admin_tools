(function(){
    /**
     * Angular service for sharing data needed for rendering and controlling errors across controllers.
     */
    angular.module('app').factory('errorModel', [function(){
        return {
            hasError: false
        };
    }]);
})();
