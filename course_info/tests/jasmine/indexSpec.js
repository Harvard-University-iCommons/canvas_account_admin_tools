describe('course_info IndexController', function() {
  beforeEach(module('app'));

  var $controller;

  beforeEach(inject(function(_$controller_){
    // The injector unwraps the underscores (_) from around
    // the parameter names when matching
    $controller = _$controller_;
  }));

  it("should inject the controller so it's available to the tests", function() {
    expect($controller).not.toBe(null);
  });

  describe('$scope.checkIfSearchable', function() {
    it('should load the controller without errors', function() {
      var $scope = {};
      var dummyElement = document.createElement('div');
      dummyElement.innerText = '{}';
      spyOn(document, 'getElementById').and.returnValue(dummyElement);
      var controller = $controller('IndexController', { $scope: $scope });
      expect(controller).not.toBe(null);
    });
  });
});