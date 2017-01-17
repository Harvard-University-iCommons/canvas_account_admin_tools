describe('PublishCoursesAPIService test', function () {
  var pcapi, $httpBackend, $http, $log, $q;
  var djangoUrl;  // required by pcapi; mock these

  beforeEach(module(function mockDjangoUrl($provide) {
    djangoUrl = {
      reverse: function (viewName, args) { return 'fake-url' }
    };
    $provide.value('djangoUrl', djangoUrl)
  }));

  beforeEach(function setupTestEnvironment() {
    module('PublishCoursesAPIModule');
    inject(function (_$httpBackend_, _pcapi_, _$http_, _$log_, _$q_) {
      pcapi = _pcapi_;
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
    this.getParamsAndRespondWith = spec.getParamsAndRespondWith;
  });

  afterEach(spec.verifyNoOutstanding);

  describe('Sanity check on dependency injection', function () {
    it('injects the providers we requested', function () {
      spec.diSanityCheck([$httpBackend, $http, $q, $log, pcapi]);
    });
  });

  describe('getCourseSummary', function () {
    it('GETs course summary with expected params', function () {
      var accountId = 1;
      var termId = 2;
      var actualData = null;
      var apiResponse = {test: 'ok'};

      pcapi.CourseSummary.get(accountId, termId).then(function (data) {
        actualData = data;
      });

      var options = {method: 'GET', response: apiResponse};

      var actualParams = this.getParamsAndRespondWith(options);

      expect(actualData.test).toBe('ok');
      // $httpBackend decodes URI to get values, all have been cast to String
      expect(actualParams).toEqual(
        {account_id: String(accountId), term_id: String(termId)});
    });
    it('cancels pending request');
    it('returns data on success');
    it('resets pending request tracker on success');
    it('stops error propagation for canceled pending requests');
    it('reports status text on non-canceled error');
  });
  describe('createJob', function () {
    it('POSTs job with expected params', function () {
      var accountId = 1;
      var termId = 2;
      var expectedContent = {account: accountId, term: termId};

      pcapi.Jobs.create(accountId, termId);

      // this asserts, via $httpBackend.expect, that the API is sending
      // expectedContent to the server
      var options = {method: 'POST', content: expectedContent, statusCode: 201};
      this.getParamsAndRespondWith(options);
    });
    it('returns async promise that resolves on success with data');
    it('returns status text on error');
  });
});
