describe('IndexController test', function () {
  var $controller, $rootScope, $log, AppConfig, $httpBackend, $q;
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
    $provide.value('actrapi', actrapi);
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
    $provide.value('pcapi', pcapi);
  }));

  beforeEach(function setupTestEnvironment() {
    // load the app and the templates-as-module
    module('PublishCourses');
    module('templates');
    angular.module('PublishCourses').constant("DjangoContextData", {
      resource_link_id: 'abc123',
      school: 'colgsas'
    });

    inject(function (_$controller_, _$rootScope_, _$log_, _$q_,
                     _AppConfig_, _$httpBackend_) {
      $controller = _$controller_;
      $httpBackend = _$httpBackend_;
      $rootScope = _$rootScope_;
      $log = _$log_;
      $q = _$q_;
      AppConfig = _AppConfig_;
    });
    scope = $rootScope.$new();
    controller = $controller('IndexController', {$scope: scope, actrapi: actrapi, pcapi: pcapi});
    $httpBackend.expectGET(/partials\/list\.html.*/).respond(200, {});
    $httpBackend.flush(1);
  });

  describe('Sanity check on dependency injection', function () {
    it('injects the providers we requested', function () {
      spec.diSanityCheck([$controller, $rootScope, $log, AppConfig, $httpBackend]);
    });
  });

  /* Main test methods */

  fdescribe('initialize', function () {
    beforeEach(function() {
      this.school = {id: 'colgsas'};
      this.terms = {
        // for term end date tests
        pastByConcludeDate: {conclude_date: '1999', end_date: '2100'},
        pastByEndDate: {end_date: '1999'},
        currentByConcludeDate: {conclude_date: '2100', end_date: '1999'},
        currentByEndDate: {end_date: '2100'},
        // for term code tests
        normalTermCode: {term_code: 1, conclude_date: '2100'},
        ongoingTermCode: {term_code: 99, conclude_date: '2100'}
      };
      this.termList = [];
      angular.forEach(this.terms, function(value, key) {
        this.push(value);  // key is just descriptive; value is the term object
      }, this.termList);

      this.getSchool = $q.defer();
      this.getTerms = $q.defer();
      spyOn(actrapi.Schools, 'get').and.returnValue(this.getSchool.promise);
      spyOn(actrapi.Terms, 'getList').and.returnValue(this.getTerms.promise);

      this.controllerInitialize = function() {
        this.getSchool.resolve(this.school);
        this.getTerms.resolve(this.termList);
        scope.initialize();
        scope.$digest();
      }
    });
    it('shows school short title if available', function () {
      this.school.title_short = 'short title';
      this.controllerInitialize();
      expect(scope.school.name).toEqual(this.school.title_short);
    });
    it('shows school long title if short title available', function () {
      this.school.title_long = 'long title';
      this.controllerInitialize();
      expect(scope.school.name).toEqual(this.school.title_long);
    });
    it('shows school id if no titles are available', function () {
      this.controllerInitialize();
      expect(scope.school.name).toEqual(this.school.id);
    });
    it('shows only current terms in dropdown', function() {
      this.controllerInitialize();
      var t = this.terms;
      expect(scope.terms).toContain(t.currentByConcludeDate);
      expect(scope.terms).toContain(t.currentByEndDate);
      expect(scope.terms).not.toContain(t.pastByConcludeDate);
      expect(scope.terms).not.toContain(t.pastByEndDate);
    });
    it('excludes ongoing terms in dropdown', function() {
      this.controllerInitialize();
      var t = this.terms;
      expect(scope.terms).toContain(t.normalTermCode);
      expect(scope.terms).not.toContain(t.ongoingTermCode);
    });
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
