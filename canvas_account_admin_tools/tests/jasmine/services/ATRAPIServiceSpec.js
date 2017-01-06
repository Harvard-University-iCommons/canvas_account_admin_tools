describe('ATRAPIService test', function () {
    var atrapi, $httpBackend, $http, $log, $q;
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
        inject(function (_$httpBackend_, _atrapi_, _$http_, _$log_, _$q_) {
            atrapi = _atrapi_;
            $httpBackend = _$httpBackend_;
            $http = _$http_;
            $log = _$log_;
            $q = _$q_;
        });
    });

    describe('Sanity check on dependency injection', function() {
        it('injects the providers we requested', function () {
            [$httpBackend, $http, $q, $log, atrapi].forEach(function (thing) {
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
