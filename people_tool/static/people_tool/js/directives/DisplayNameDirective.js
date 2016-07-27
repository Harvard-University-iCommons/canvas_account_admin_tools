(function () {
    var app = angular.module('PeopleTool');

    app.directive('displayname', function() {
        return {
            restrict: 'E',
            scope: {
                firstname: '@',
                lastname: '@',
                univid: '@',

            },
            controller: function($scope) {
                $scope.formatName = function(firstname, lastname, univid) {
                    <!-- If first and  last name are both null, display the univ_id-->
                    var displayname = "";
                    if (!firstname && !lastname) {
                        displayname = univid;
                    } else {
                        if (lastname) {
                            displayname =lastname;
                            //Only add teh comma if the first name also exists
                            if (firstname) {
                                displayname = displayname + ", ";
                            }
                        }
                        if (firstname) {
                            displayname = displayname + firstname;
                        }
                    }
                    return displayname;
                };
            },
            template: '<span>{{ formatName(firstname, lastname, univid)}}</span>',
        };
    });
})();
