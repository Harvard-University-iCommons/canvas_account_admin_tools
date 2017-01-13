describe('resourceLinkConfigService test', function () {
    var $httpBackend, $window, $httpProvider, $http;
    var mockAppend;

    beforeEach(function setupTestEnvironment() {
        module(function(_$httpProvider_) {
            $httpProvider = _$httpProvider_;
            spyOn($httpProvider.interceptors, 'push').and.callThrough();
        });
        module('resourceLinkConfigModule');
        inject(function (_$window_, _$httpBackend_, _$http_) {
            $window = _$window_;
            $httpBackend = _$httpBackend_;
            $http = _$http_;
        });
        mockAppend = jasmine.createSpy('append_resource_link_id');
        var globals = jasmine.getGlobal();
        globals['append_resource_link_id'] = mockAppend;
    });

    afterEach(function() {
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('Sanity check on dependency injection', function() {
        it('injects the providers we requested', function () {
            [$window, $httpBackend, $http].forEach(function (thing) {
                expect(thing).not.toBeUndefined();
                expect(thing).not.toBeNull();
            });
        });
    });

    /* Main test methods */

    // todo: get the references to `window` working, or move append_resource_link_id() out of window.globals() context
    describe('Resource link ID interceptor', function() {
        it('is added at config time', function() {
            expect($httpProvider.interceptors.push)
              .toHaveBeenCalledWith('resourceLinkInterceptor');
        });
        xit('calls append_resource_link_id() for app resources', function() {
            $http.get('app/resource.html');
            $httpBackend.expectGET('app/resource.html').respond({});
            $httpBackend.flush();
            expect($window.globals.append_resource_link_id).toHaveBeenCalled();
        });
        xit('skips append_resource_link_id() for static resources', function() {
            $http.get('/uib/template/static-resource.html');
            $httpBackend.expectGET('/uib/template/static-resource.html').respond({});
            $httpBackend.flush();
            expect($window.globals.append_resource_link_id).not.toHaveBeenCalled();
        });
    });
});
