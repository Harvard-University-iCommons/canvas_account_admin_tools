describe('PublishCoursesAPIService test', function() {
    var pcapi, $httpBackend, $http, $log, $q;
    var djangoUrl;  // required by pcapi; mock these

    beforeEach(module(function mockDjangoUrl($provide) {
        djangoUrl = {reverse: function() {}};
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

    describe('Sanity check on dependency injection', function() {
        it('injects the providers we requested', function () {
            [$httpBackend, $http, $q, $log, pcapi].forEach(function (thing) {
                expect(thing).not.toBeUndefined();
                expect(thing).not.toBeNull();
            });
        });
    });

    describe('getCourseSummary', function() {
        it('GETs course summary with expected params');
        it('cancels pending request');
        it('returns data on success');
        it('resets pending request tracker on success');
        it('stops error propagation for canceled pending requests');
        it('reports status text on non-canceled error');
    });
    describe('createJob', function() {
        it('POSTs job with expected params');
        it('returns async promise that resolves on success with data');
        it('returns status text on error');
    });
});
