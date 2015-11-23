// NOTE - this is still a work in progress, doesn't really test anything useful

describe('course_info SearchController', function() {
  beforeEach(module('CourseInfo'));

  var $controller, $window, $document, $httpBackend, $rootScope;
  var scope, controller;

  beforeEach(inject(function(_$controller_, _$window_, _$document_, _$httpBackend_, _$rootScope_){
    // The injector unwraps the underscores (_) from around
    // the parameter names when matching
    $controller = _$controller_;
    $window = _$window_;
    $document = _$document_;
    $httpBackend = _$httpBackend_;
    $rootScope = _$rootScope_;

    // this comes from django_auth_lti, just stub it out so that the $httpBackend
    // sanity checks in afterEach() don't fail
    $window.globals = {
        append_resource_link_id: function(url) { return url; },
    };

    // instantiate the controller, give it a $scope
    scope = $rootScope.$new();
    controller = $controller('SearchController', { $scope: scope });

    // always expect the controller constructor to call for term codes
    var term_codes = {
        "results": [
            {
                "term_code": 0,
                "term_name": "Summer",
                "sort_order": 40
            },
            {
                "term_code": 1,
                "term_name": "Fall",
                "sort_order": 60
            },
            {
                "term_code": 2,
                "term_name": "Spring",
                "sort_order": 30
            },
        ],
    };
    $httpBackend.expectGET('/icommons_rest_api/api/course/v2/term_codes/?limit=100')
        .respond(200, JSON.stringify(term_codes));
    $httpBackend.flush(1); // flush the term_codes request
  }));

  it("should inject the providers we've requested", function() {
    [null, undefined].forEach(function(bad) {
        expect($controller).not.toBe(bad);
        expect($window).not.toBe(bad);
        expect($document).not.toBe(bad);
        expect($httpBackend).not.toBe(bad);
        expect($rootScope).not.toBe(bad);
    });
  });

  it("should instantiate the controller", function() {
    expect(controller).not.toBe(null);
  });

  afterEach(function() {
    // sanity checks to make sure no http work is still pending
    $httpBackend.verifyNoOutstandingExpectation();
    $httpBackend.verifyNoOutstandingRequest();
  });

  describe('$scope setup', function() {
      
  });

  describe('$scope.enableColumnSorting()', function() {

  });

  describe('$scope.courseInstanceToTable()', function() {

  });

  describe('$scope.initializeDatatable()', function() {

  });

  describe('$scope.searchCourseInstances()', function() {

  });
});
