describe('PendingHandler test', function () {
  var $http, $httpBackend, pendingInterceptor;

  beforeEach(function setupTestEnvironment() {
    module(function (_$httpProvider_) {
      $httpProvider = _$httpProvider_;
      spyOn($httpProvider.interceptors, 'push').and.callThrough();
    });
    module('pendingHandlerModule');
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
    it('injects the providers we requested', function () {
      spec.diSanityCheck([$http, $httpBackend, pendingInterceptor]);
    });
  });

  describe('pending handler interceptor', function () {
    it('is added at config time', function () {
      expect($httpProvider.interceptors.push)
        .toHaveBeenCalledWith('pendingInterceptor');
    });
  });

  describe('pending request resolution', function () {
    beforeEach(function() {
      this.callData = [];
      var saveCallData = function(data) { this.callData.push(data.data) };
      this.saveCallData = saveCallData.bind(this);
    });
    it('cancels pending request when tag is used', function() {
      var config = {pendingRequestTag: 'only one!'};
      $http.get('abc', config).then(this.saveCallData);
      $http.get('abc', config).then(this.saveCallData);
      $httpBackend.expectGET('abc').respond(200, 'ok');
      $httpBackend.expectGET('abc').respond(200, 'ok');
      $httpBackend.flush(1);  // second one was canceled

      expect(this.callData.length).toEqual(1);
      expect(this.callData[0]).toEqual('ok');
    });
    it('runs requests in parallel when tag is omitted', function() {
      $http.get('abc').then(this.saveCallData);
      $http.get('abc').then(this.saveCallData);
      $httpBackend.expectGET('abc').respond(200, 'ok');
      $httpBackend.expectGET('abc').respond(200, 'ok');
      $httpBackend.flush(2);

      expect(this.callData.length).toEqual(2);
      expect(this.callData[0]).toEqual('ok');
      expect(this.callData[1]).toEqual('ok');
    });
    it('runs requests in parallel if using different tags', function() {
      var configs = [{pendingRequestTag: 'one!'}, {pendingRequestTag: 'two!'}];
      $http.get('abc', configs[0]).then(this.saveCallData);
      $http.get('abc', configs[1]).then(this.saveCallData);
      $httpBackend.expectGET('abc').respond(200, 'ok');
      $httpBackend.expectGET('abc').respond(200, 'ok');
      $httpBackend.flush(2);

      expect(this.callData.length).toEqual(2);
      expect(this.callData[0]).toEqual('ok');
      expect(this.callData[1]).toEqual('ok');
    });
  });
});
