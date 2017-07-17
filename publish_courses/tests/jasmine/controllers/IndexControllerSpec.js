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
      CourseList: { get: function () { return $q.defer().promise }},
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
    controller = $controller('IndexController',
      {$scope: scope, actrapi: actrapi, pcapi: pcapi});
    $httpBackend.expectGET(/partials\/list\.html.*/).respond(200, {});
    $httpBackend.flush(1);
    this.$httpBackend = $httpBackend;  // for spec helpers
  });

  afterEach(spec.verifyNoOutstanding);

  describe('Sanity check on dependency injection', function () {
    it('injects the providers we requested', function () {
      spec.diSanityCheck([$controller, $rootScope, $log, AppConfig, $httpBackend]);
    });
  });

  /* Main test methods */

  describe('initialize', function () {
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

  describe('loadCourseData', function () {
    beforeEach(function() {
      this.school = scope.school = {id: 'abc'};
      this.term = scope.selectedTerm = {meta_term_id: '2020-1'};
    });
    it('requests course summary with expected data', function() {
      spyOn(pcapi.CourseList, 'get').and.callThrough();
      scope.loadCourseData();
      expect(pcapi.CourseList.get)
        .toHaveBeenCalledWith(this.school.id, this.term.meta_term_id);
    });
    it('makes expected response data available to UI', function() {
      var testData = {
        'course_summary': {'test': 'ok'},
        'canvas_url': 'test_url',
        'courses': []};
      var d = $q.defer();
      d.resolve(testData);
      spyOn(pcapi.CourseList, 'get').and.returnValue(d.promise);
      scope.loadCourseData();
      scope.$digest();

      expect(scope.coursesSummary).toEqual({'test': 'ok'});
      expect(scope.dataTable).not.toBe(null);
    });
  });

  describe('publish', function () {
    beforeEach(function() {
      this.school = scope.school = {id: 'abc'};
      this.term = scope.selectedTerm = {meta_term_id: '2020-1'};
      this.setupSuccessfulJob = function() {
        var testData = {test: 'ok'};
        var d = $q.defer();
        d.resolve(testData);
        spyOn(pcapi.Jobs, 'create').and.returnValue(d.promise);
      };
      this.setupFailedJob = function() {
        var testData = {test: 'failed'};
        var d = $q.defer();
        d.reject(testData);
        spyOn(pcapi.Jobs, 'create').and.returnValue(d.promise);
      };
    });
    it('notifies user when successful', function() {
      this.setupSuccessfulJob();
      scope.publish();
      scope.$digest();
      expect(scope.message).toEqual(scope.messages.success);
    });
    it('notifies user when unsuccessful', function() {
      this.setupFailedJob();
      scope.publish();
      scope.$digest();
      expect(scope.message).toEqual(scope.messages.failure);
    });
    it('turns off operationInProgress when successful', function() {
      this.setupSuccessfulJob();
      scope.publish();
      expect(scope.operationInProgress).toBe(true);
      scope.$digest();
      expect(scope.operationInProgress).toBe(false);
    });
    it('turns off operationInProgress when unsuccessful', function() {
      this.setupFailedJob();
      scope.publish();
      expect(scope.operationInProgress).toBe(true);
      scope.$digest();
      expect(scope.operationInProgress).toBe(false);
    });
    it('publishes all courses in a term', function() {
      this.setupSuccessfulJob();
      scope.publish();
      expect(pcapi.Jobs.create)
        .toHaveBeenCalledWith(this.school.id, this.term.meta_term_id, null);
    });
    it('publishes only selected courses', function() {
      var course1 = {'id': 1, 'name': 'test course'};
      var course2 = {'id': 2, 'name': 'second test course'};
      scope.addSelectedCourse(course1);
      scope.addSelectedCourse(course2);
      this.setupSuccessfulJob();
      scope.publish();
      expect(pcapi.Jobs.create)
        .toHaveBeenCalledWith(this.school.id, this.term.meta_term_id, [1, 2]);
    });

  });

  describe('DataTable', function () {
    beforeEach(function() {
      this.course1 = {'id': 1, 'name': 'test course'};
      this.course2 = {'id': 2, 'name': 'second test course'};
      this.course3 = {'id': 3, 'name': 'third test course'};
    });

    it('will add the selected course to the selected courses dict', function() {
      scope.addSelectedCourse(this.course1);
      expect(scope.selectedCourses).toEqual({1: this.course1});

      scope.addSelectedCourse(this.course2);
      expect(scope.selectedCourses).toEqual({1: this.course1, 2: this.course2});
    });

    it('will remove the selected course from the selected courses dict', function() {
      scope.addSelectedCourse(this.course1);
      scope.removeSelectedCourse(this.course1);
      expect(scope.selectedCourses).toEqual({});

      scope.addSelectedCourse(this.course1);
      scope.addSelectedCourse(this.course2);
      scope.removeSelectedCourse(this.course2);
      expect(scope.selectedCourses).toEqual({1: this.course1});
    });


    it('gets the count of selected courses', function() {
      expect(scope.getSelectedCourseIdsCount()).toEqual(0);

      scope.addSelectedCourse(this.course1);
      scope.addSelectedCourse(this.course2);
      expect(scope.getSelectedCourseIdsCount()).toEqual(2);

    });

    it('gets the list of ids for the selected courses', function() {
      expect(scope.getSelectedCourses()).toEqual([]);

      scope.addSelectedCourse(this.course1);
      scope.addSelectedCourse(this.course2);
      scope.addSelectedCourse(this.course3);
      expect(scope.getSelectedCourses()).toEqual([1, 2, 3]);

      scope.removeSelectedCourse(this.course2);
      expect(scope.getSelectedCourses()).toEqual([1, 3]);
    });

    it('gets the label that is displayed on the publish button', function() {
      expect(scope.getPublishButtonMessage()).toEqual('All');

      scope.addSelectedCourse(this.course1);
      expect(scope.getPublishButtonMessage()).toEqual('Selected');

      scope.removeSelectedCourse(this.course1);
      expect(scope.getPublishButtonMessage()).toEqual('All');
    });
  });

});
