(function () {
    var module = angular.module('TermDropdownDirective', []);
    module.directive('termDropdown', function() {
        return {
            restrict: 'E',
            templateUrl: 'partials/term-dropdown.html',
            scope: {
                terms: '=',  // list (empty=no data), or null if not loaded
                onSelect: '&'
            },
            controller: function($scope) {
                $scope.selectedTerm = null;
                $scope.dropdownText = '';

                $scope.getTermDisplayText = function() {
                    if (angular.isArray($scope.terms)) {
                        if ($scope.selectedTerm) {
                            return $scope.selectedTerm.display_name
                                + ' <span class="caret"></span>';
                        } else if ($scope.terms.length > 0) {
                            return 'Choose a term'
                                + ' <span class="caret"></span>';
                        } else {
                            return 'No active terms';
                        }
                    } else {
                        return 'Loading terms...'
                            + ' <i class="fa fa-refresh fa-spin"></i>';
                    }
                };
                $scope.selectTerm = function (selectedTermIndex) {
                    $scope.selectedTerm = $scope.terms[selectedTermIndex];
                    $scope.dropdownText = $scope.getTermDisplayText();
                    $scope.onSelect({term: $scope.selectedTerm});
                };
                $scope.updateDropdownText = function() {
                    $scope.dropdownText = $scope.getTermDisplayText();
                };
            },
            link: function($scope, element, attrs) {
                $scope.$watch(attrs.terms, $scope.updateDropdownText);
            }
        };
    });
})();
