describe('resourceLinkInterceptor test', function () {
  var $httpBackend, $httpProvider, $http;

  beforeEach(function setupTestEnvironment() {
    this.resource_link_id = 'abc123';
    this.resource_link_id_string = 'resource_link_id=' + this.resource_link_id;
    module(function (_$httpProvider_) {
      $httpProvider = _$httpProvider_;
      spyOn($httpProvider.interceptors, 'push').and.callThrough();
    });
    module('resourceLinkModule');
    angular.module('resourceLinkModule').constant("DjangoContextData", {
      resource_link_id: this.resource_link_id
    });
    inject(function (_$httpBackend_, _$http_) {
      $httpBackend = _$httpBackend_;
      $http = _$http_;
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
      spec.diSanityCheck([$httpBackend, $http]);
    });
  });

  /* Main test methods */

  describe('Resource link ID interceptor', function () {
    it('is added at config time', function () {
      expect($httpProvider.interceptors.push)
        .toHaveBeenCalledWith('resourceLinkInterceptor');
    });
    it('calls append_resource_link_id() for app resources', function () {
      var resource = 'app/resource.html';
      var expectedUrl = resource + '?' + this.resource_link_id_string;
      $http.get(resource);
      $httpBackend.expectGET(expectedUrl).respond({});
      $httpBackend.flush();
    });
    it('skips append_resource_link_id() for static resources', function () {
      var resource = 'uib/template/static-resource.html';
      $http.get(resource);
      $httpBackend.expectGET(resource).respond({});
      $httpBackend.flush();
    });
  });
});
