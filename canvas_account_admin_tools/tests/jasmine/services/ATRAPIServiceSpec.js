describe('ATRAPIService test', function () {
    var atrapi, httpBackend;
    var angularDRF, djangoUrl;  // required by atrapi; mock these

    /* Setup, teardown, sanity checks */
    beforeEach(module(function mockAngularDRF($provide) {
        angularDRF = {get: function() {}};
        $provide.value('angularDRF', angularDRF)
    }));

    beforeEach(module(function mockDjangoUrl($provide) {
        djangoUrl = {reverse: function() {}};
        $provide.value('djangoUrl', djangoUrl)
    }));

    beforeEach(function setupTestEnvironment() {
        module('ATRAPIModule');
        inject(function ($httpBackend, _atrapi_) {
            atrapi = _atrapi_;
            httpBackend = $httpBackend;
        });
    });

    describe('Sanity check on dependency injection', function() {
        it('injects the providers we requested', function () {
            [httpBackend, atrapi].forEach(function (thing) {
                expect(thing).not.toBeUndefined();
                expect(thing).not.toBeNull();
            });
        });
    });

    /* Main test methods */

    describe('Schools', function() {
        it('gets school from API with expected params');
        it('cancels pending request when when tag is used');
        it('runs requests in parallel when tag is omitted');
        it('runs requests in parallel if using different tags');
    });
    describe('Terms', function() {
        it('gets terms from API with expected params');
        it('uses defaults by default');
        it('skips defaults if explicitly requested');
        it('overrides defaults with custom params');
    });

});
