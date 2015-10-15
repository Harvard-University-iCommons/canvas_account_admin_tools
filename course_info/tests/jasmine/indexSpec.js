describe('course_info IndexController', function() {
  beforeEach(module('app'));

  var $controller, $window, $document;

  beforeEach(inject(function(_$controller_, _$window_, _$document_){
    // The injector unwraps the underscores (_) from around
    // the parameter names when matching
    $controller = _$controller_;
    $window = _$window_;
    $document = _$document_;
  }));

  it("should inject the controller so it's available to the tests", function() {
    expect($controller).not.toBe(null);
  });

  describe('$scope.checkIfSearchable', function() {
    it('should load the controller without errors', function() {
      var $scope = {$watch: function() {}};
      var controller = $controller('IndexController', { $scope: $scope });
      expect(controller).not.toBe(null);
    });
  });
});
