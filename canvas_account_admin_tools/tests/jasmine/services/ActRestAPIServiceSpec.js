describe('ActRestAPIService test', function () {
  var actrapi, $httpBackend, $http, $log, $q;
  var angularDRF, djangoUrl;  // required by actrapi; mock these

  /* Setup, teardown, sanity checks */
  beforeEach(module(function mockAngularDRF($provide) {
    angularDRF = {
      // this provides a promise interface to satisfy catch(), then(), etc
      // to actually resolve the promise, spyOn().and.returnValue() with a
      // promise controlled by the test code
      get: function () { return $q.defer().promise }
    };
    $provide.value('angularDRF', angularDRF)
  }));

  beforeEach(module(function mockDjangoUrl($provide) {
    djangoUrl = {
      reverse: function (viewName, args) { return 'fake-url' }
    };
    $provide.value('djangoUrl', djangoUrl)
  }));

  beforeEach(function setupTestEnvironment() {
    module('ActRestAPIModule');
    inject(function (_$httpBackend_, _actrapi_, _$http_, _$log_, _$q_) {
      actrapi = _actrapi_;
      $httpBackend = _$httpBackend_;
      $http = _$http_;
      $log = _$log_;
      $q = _$q_;
    });
  });

  beforeEach(function() {
    // save references to injected services in `this` (jasmine user context)
    // so they can be accessed by spec helpers
    this.$httpBackend = $httpBackend;
    // spec helper functions that require a jasmine user context need to be
    // called under that context, so store references that retain the context
    this.getParamsAndRespondWith = spec.getParamsAndRespondWith;
  });

  afterEach(spec.verifyNoOutstanding);

  describe('Sanity check on dependency injection', function () {
    it('injects the providers we requested', function () {
      spec.diSanityCheck([$httpBackend, $http, $q, $log, actrapi]);
    });
  });

  /* Main test methods */

  describe('Schools', function () {
    it('gets school from API with expected params', function () {
      var schoolName = 'abc';
      var actualData = null;
      var options = {response: {id: schoolName}};

      actrapi.Schools.get(schoolName).then(function(data) {
        actualData = data;
      });

      var actualParams = this.getParamsAndRespondWith(options);

      expect(actualData.id).toBe(schoolName);
      expect(actualParams).toEqual({});
    });
  });

  describe('Terms', function () {
    it('gets terms from API with expected params', function() {
      var expectedConfig = actrapi.Terms.defaultConfig;

      spyOn(angularDRF, 'get').and.callThrough();

      actrapi.Terms.getList();

      expect(angularDRF.get)
        .toHaveBeenCalledWith(jasmine.any(String), expectedConfig);
    });
  });

  describe('default params', function () {
    var resources = ['Schools', 'Terms'];
    var expected = {};

    beforeEach(function() {
      spyOn(angularDRF, 'get').and.callThrough();
      angular.forEach(resources, function(r) {
        expected[r] = {params: {fetch: r}};
        actrapi[r].defaultConfig = expected[r];
      });
    });

    it('uses configurable defaults by default for Schools', function() {
      actrapi.Schools.get('abc');
      expect(this.getParamsAndRespondWith())
        .toEqual(expected['Schools'].params);
    });
    it('uses configurable defaults by default for Terms', function() {
      actrapi.Terms.getList();
      expect(angularDRF.get)
        .toHaveBeenCalledWith(jasmine.any(String), expected['Terms']);
    });
    it('skips defaults if explicitly requested', function() {
      actrapi.Terms.getList({useDefaults: false});
      expect(angularDRF.get)
        .toHaveBeenCalledWith(jasmine.any(String), {});
    });
    it('overrides defaults with custom params', function() {
      var customConfig = {config: {params: {fetch: 'something'}}};
      actrapi.Terms.getList(customConfig);
      expect(angularDRF.get)
        .toHaveBeenCalledWith(jasmine.any(String), customConfig.config);
    });
  });

  describe('config', function () {
    it('generates URLs using configurable baseUrl', function() {
      var defaultBaseUrl = actrapi.config.baseUrl;
      var customBaseUrl = 'my/new/api/base/';
      actrapi.config.baseUrl = customBaseUrl;

      spyOn(djangoUrl, 'reverse').and.callThrough();

      actrapi.Terms.getList();

      expect(djangoUrl.reverse)
        .toHaveBeenCalledWith(jasmine.any(String),[jasmine.any(String)]);
      var secondArg = djangoUrl.reverse.calls.first().args[1];
      // actual arg is an array, URL is first element in it
      var constructedUrl = secondArg[0];
      expect(constructedUrl).toContain(customBaseUrl);
      expect(constructedUrl).not.toContain(defaultBaseUrl);
    });

    it('allows overriding GET defaults', function() {
      var expectedConfig = {params: {something: 'else'}};
      actrapi.Terms.defaultConfig = expectedConfig;

      spyOn(angularDRF, 'get').and.callThrough();

      actrapi.Terms.getList();

      expect(angularDRF.get)
        .toHaveBeenCalledWith(jasmine.any(String), expectedConfig);
    });
  });

  // todo: move these into PendingInterceptorSpec.js
  describe('pending request resolution', function () {
    var firstCall = null;
    var secondCall = null;
    var testData = {test: 'ok'};
    var backendExpectationDetails = {response: testData, flushLater: true};

    beforeEach(function () {
      firstCall = null;
      secondCall = null;
    });

    // todo: fix this failing test
    xit('cancels pending request when tag is used', function () {
      var options = {pendingRequestTag: 'only one!'};
      actrapi.Schools.get('abc', options).then(function (data) {
        firstCall = data;
      });
      actrapi.Schools.get('abc', options).then(function (data) {
        secondCall = data;
      });
      this.getParamsAndRespondWith(backendExpectationDetails);
      this.getParamsAndRespondWith(backendExpectationDetails);
      $httpBackend.flush(1);  // second one was canceled

      expect(firstCall).toBe(null);
      expect(secondCall).toEqual(testData);
    });
    it('runs requests in parallel when tag is omitted', function () {
      actrapi.Schools.get('abc').then(function (data) {
        firstCall = data;
      });
      actrapi.Schools.get('abc').then(function (data) {
        secondCall = data;
      });
      this.getParamsAndRespondWith(backendExpectationDetails);
      this.getParamsAndRespondWith(backendExpectationDetails);
      $httpBackend.flush(2);

      expect(firstCall).toEqual(testData);
      expect(secondCall).toEqual(testData);
    });
    it('runs requests in parallel if using different tags', function () {
      var optionsOne = {pendingRequestTag: 'request one!'};
      var optionsTwo = {pendingRequestTag: 'request two!'};
      actrapi.Schools.get('abc', optionsOne).then(function (data) {
        firstCall = data;
      });
      actrapi.Schools.get('abc', optionsTwo).then(function (data) {
        secondCall = data;
      });
      this.getParamsAndRespondWith(backendExpectationDetails);
      this.getParamsAndRespondWith(backendExpectationDetails);
      $httpBackend.flush(2);

      expect(firstCall).toEqual(testData);
      expect(secondCall).toEqual(testData);
    });
  });
});
