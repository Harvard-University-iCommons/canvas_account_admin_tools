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

  afterEach(function () {
    // sanity checks to make sure no http calls are still pending
    $httpBackend.verifyNoOutstandingExpectation();
    $httpBackend.verifyNoOutstandingRequest();
  });

  describe('Sanity check on dependency injection', function () {
    it('injects the providers we requested', function () {
      [$httpBackend, $http, $q, $log, actrapi].forEach(function (thing) {
        expect(thing).not.toBeUndefined();
        expect(thing).not.toBeNull();
      });
    });
  });

  var getSchoolGETParamsAndRespondWith = function(apiResponse, flushLater) {
    var actualParams = null;
    $httpBackend.expectGET(/.*/).respond(function (m, u, d, h, params) {
      actualParams = params;
      return [200, apiResponse];
    });
    if (!flushLater) { $httpBackend.flush(1); };
    return actualParams;
  };

  /* Main test methods */

  describe('Schools', function () {
    it('gets school from API with expected params', function () {
      var schoolName = 'abc';
      var actualData = null;
      var apiResponse = {id: schoolName};

      actrapi.Schools.get(schoolName).then(function(data) {
        actualData = data;
      });

      var actualParams = getSchoolGETParamsAndRespondWith(apiResponse);

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

  describe('pending request resolution', function () {
    var firstCall = null;
    var secondCall = null;
    var testData = {test: 'ok'};

    beforeEach(function() {
      firstCall = null;
      secondCall = null;
    });

    it('cancels pending request when tag is used', function() {
      actrapi.Schools.get('abc', 'only one!').then(function(data){
        firstCall=data;
      });
      actrapi.Schools.get('abc', 'only one!').then(function(data){
        secondCall=data;
      });
      getSchoolGETParamsAndRespondWith(testData, true);
      getSchoolGETParamsAndRespondWith(testData, true);
      $httpBackend.flush(1);  // second one was canceled

      expect(firstCall).toBe(null);
      expect(secondCall).toEqual(testData);
    });
    it('runs requests in parallel when tag is omitted', function() {
      actrapi.Schools.get('abc').then(function(data){
        firstCall=data;
      });
      actrapi.Schools.get('abc').then(function(data){
        secondCall=data;
      });
      getSchoolGETParamsAndRespondWith(testData, true);
      getSchoolGETParamsAndRespondWith(testData, true);
      $httpBackend.flush(2);

      expect(firstCall).toEqual(testData);
      expect(secondCall).toEqual(testData);
    });
    it('runs requests in parallel if using different tags', function() {
      actrapi.Schools.get('abc', 'request one!').then(function(data){
        firstCall=data;
      });
      actrapi.Schools.get('abc', 'request two!').then(function(data){
        secondCall=data;
      });
      getSchoolGETParamsAndRespondWith(testData, true);
      getSchoolGETParamsAndRespondWith(testData, true);
      $httpBackend.flush(2);

      expect(firstCall).toEqual(testData);
      expect(secondCall).toEqual(testData);
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

    it('uses configurable defaults by default', function() {
      actrapi.Schools.get('abc');
      actrapi.Terms.getList();

      var actualSchoolParams = getSchoolGETParamsAndRespondWith({});

      expect(actualSchoolParams).toEqual(expected['Schools'].params);
      expect(angularDRF.get)
        .toHaveBeenCalledWith(jasmine.any(String), expected['Terms']);
    });
    it('skips defaults if explicitly requested', function() {
      actrapi.Terms.getList(null, false);
      expect(angularDRF.get)
        .toHaveBeenCalledWith(jasmine.any(String), {});
    });
    it('overrides defaults with custom params', function() {
      var customConfig = {params: {fetch: 'something'}};
      actrapi.Terms.getList(customConfig);
      expect(angularDRF.get)
        .toHaveBeenCalledWith(jasmine.any(String), customConfig);
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

});