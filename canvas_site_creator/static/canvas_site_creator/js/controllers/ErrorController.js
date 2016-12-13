(function(){
    /**
     * Angular controller for displaying errors.
     */
    angular.module('app').controller('ErrorController', ['$scope', 'errorModel', function($scope, errorModel){
        $scope.errorModel = errorModel;

        // Output DataTable AJAX errors to the browser console instead of as Javascript alerts
        $.fn.dataTable.ext.errMode = function(settings, helpPage, message){
            console.log(message);
            $scope.errorModel.hasError = true;
            $scope.$apply();
        };
    }]);
})();
