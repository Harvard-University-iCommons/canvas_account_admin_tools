describe('PendingHandler test', function () {
  var $http, $httpBackend, pendingInterceptor;

  beforeEach(function setupTestEnvironment() {
    module('PendingHandlerModule');
    inject(function (_$http_, _$httpBackend_, _pendingInterceptor_) {
      $http = _$http_;
      $httpBackend = _$httpBackend_;
      pendingInterceptor = _pendingInterceptor_;
    });
  });

  beforeEach(function() {
    // save references to injected services in `this` (jasmine user context)
    // so they can be accessed by spec helpers
    this.$httpBackend = $httpBackend;
  });

  afterEach(spec.verifyNoOutstanding);

  describe('Sanity check on dependency injection', function () {
    xit('injects the providers we requested', function () {
      spec.diSanityCheck([$http, $httpBackend, pendingInterceptor]);
    });
  });

  xdescribe('pending request resolution', function () {
    it('cancels pending request when tag is used');
    it('runs requests in parallel when tag is omitted');
    it('runs requests in parallel if using different tags');
  });
});