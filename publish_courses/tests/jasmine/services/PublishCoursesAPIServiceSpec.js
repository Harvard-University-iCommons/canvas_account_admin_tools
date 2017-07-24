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

    // set up common test data
    this.accountId = 1;
    this.termId = 2;
    this.actualData = null;
    this.apiResponse = {test: 'ok'};

    // this.getResponse, with the jasmine user context as its `this` context,
    // will be used to check the responses in individual tests
    var getResponse = function(data) { this.actualData = data; };
    this.getResponse = getResponse.bind(this);
  });

  afterEach(spec.verifyNoOutstanding);

  describe('Sanity check on dependency injection', function () {
    it('injects the providers we requested', function () {
      spec.diSanityCheck([$httpBackend, $http, $q, $log, pcapi]);
    });
  });

  describe('getCourseList', function () {
    beforeEach(function() {
      this.options = {response: this.apiResponse};
      pcapi.CourseList.get(this.accountId, this.termId)
        .then(this.getResponse);
    });
    it('GETs course list with expected params', function () {
      var actualParams = this.getParamsAndRespondWith(this.options);
      // $httpBackend decodes URI to get values, all have been cast to String
      expect(actualParams).toEqual(
        {account_id: String(this.accountId), term_id: String(this.termId)});
    });
    it('returns data on success', function() {
      this.getParamsAndRespondWith(this.options);
      expect(this.actualData).toEqual(this.apiResponse);
    });
    it('does not return data on error', function() {
      $httpBackend.expectGET(/.*/).respond(500, '');
      $httpBackend.flush(1);
      expect(this.actualData).toBeNull();
    });
  });

  describe('createJob', function () {
    beforeEach(function() {
      this.expectedContent = {account: this.accountId, term: this.termId};
      this.options = {
        method: 'POST',
        content: this.expectedContent,
        response: this.apiResponse,
        statusCode: 201};
      pcapi.Jobs.create(this.accountId, this.termId).then(this.getResponse);
    });
    it('POSTs job with expected params', function () {
      // this asserts, via $httpBackend.expect, that the API is sending
      // expectedContent to the server
      this.getParamsAndRespondWith(this.options);
    });
    it('returns data on success', function() {
      this.getParamsAndRespondWith(this.options);
      expect(this.actualData.data).toEqual(this.apiResponse);
    });
    it('does not return data on error', function() {
      $httpBackend.expectPOST(/.*/, this.expectedContent).respond(500, '');
      $httpBackend.flush(1);
      expect(this.actualData).toBeNull();
    });
  });
});
