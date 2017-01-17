describe('IndexController test', function () {
  var $controller, $rootScope, $log, AppConfig, $httpBackend;
  var actrapi, pcapi;  // required by controller; mock these
  var controller, scope;

  /* Setup, teardown, sanity checks */

  // todo: move these mock into files that describe the services?
  beforeEach(module(function mockActRestAPIService($provide) {
    actrapi = {
      // this provides a promise interface to satisfy catch(), then(), etc
      // to actually resolve the promise, spyOn().and.returnValue() with a
      // promise controlled by the test code
      Schools: { get: function () { return $q.defer().promise }},
      Terms: { getList: function () { return $q.defer().promise }}
    };
    $provide.value('actrapi', actrapi)
  }));

  // todo: move these mock into files that describe the services?
  beforeEach(module(function mockPublishCoursesAPIService($provide) {
    pcapi = {
      // this provides a promise interface to satisfy catch(), then(), etc
      // to actually resolve the promise, spyOn().and.returnValue() with a
      // promise controlled by the test code
      CourseSummary: { get: function () { return $q.defer().promise }},
      Jobs: { create: function () { return $q.defer().promise }}
    };
    $provide.value('pcapi', pcapi)
  }));

  beforeEach(function setupTestEnvironment() {
    // load the app and the templates-as-module
    module('PublishCourses');
    module('templates');
    angular.module('PublishCourses').constant("DjangoContextData", {
      school: 'colgsas'
    });

    inject(function (_$controller_, _$rootScope_, _$log_, _actrapi_,
                     _AppConfig_, _pcapi_, _$httpBackend_) {
      $controller = _$controller_;
      $httpBackend = _$httpBackend_;
      $rootScope = _$rootScope_;
      $log = _$log_;
      actrapi = _actrapi_;
      AppConfig = _AppConfig_;
      pcapi = _pcapi_;
    });
    scope = $rootScope.$new();
    controller = $controller('IndexController', {$scope: scope});
    // $scope.initialize() getting school and term
    // $httpBackend.expectGET(/.*/).respond(200, {});  // school call
    // $httpBackend.expectGET(/.*/).respond(200, []);  // term call
    // app fetching the list partial
    $httpBackend.expectGET('partials/list.html').respond(200, {});
    $httpBackend.flush(3);
  });

  describe('Sanity check on dependency injection', function () {
    it('injects the providers we requested', function () {
      spec.diSanityCheck([$controller, $rootScope, $log, actrapi, AppConfig,
        pcapi]);
    });
  });

  /* Main test methods */

  describe('initialize', function () {
    it('shows most accurate school name available', function () {
      var initializeWithSchoolData = function(schoolData) {
        $httpBackend.expectGET(/.*/).respond(200, schoolData);
        $httpBackend.expectGET(/.*/).respond(200, []);  // term call
        $scope.initialize();
        $httpBackend.flush(2);
      };

      var school = {id: 'colgsas'};
      initializeWithSchoolData(school);
      expect($scope.school.name).toEqual(school.id);

      school.title_long = 'long title';
      initializeWithSchoolData(school);
      expect($scope.school.name).toEqual(school.title_long);

      school.title_short = 'short title';
      initializeWithSchoolData(school);
      expect($scope.school.name).toEqual(school.title_short);
    });
    it('shows only current terms in dropdown');
    it('excludes ongoing terms in dropdown');
  });
  describe('loadCoursesSummary', function () {
    it('requests course summary with expected data');
    it('makes expected response data available to UI');
  });
  describe('publish', function () {
    it('notifies user when successful');
    it('notifies user when unsuccessful');
    it('creates job with expected data');
    it('turns off operationInProgress when it gets a response');
  });

});
