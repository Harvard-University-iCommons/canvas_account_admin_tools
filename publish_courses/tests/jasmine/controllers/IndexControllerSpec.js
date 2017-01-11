describe('IndexController test', function () {
    var $controller, $rootScope, $log, actrapi, AppConfig, pcapi;
    var controller, scope;

    /* Setup, teardown, sanity checks */

    beforeEach(function setupTestEnvironment() {
        // load the app and the templates-as-module
        module('PublishCourses');
        module('templates');
        angular.module('PublishCourses').constant("DjangoContextData", {
          school: 'colgsas'
        });

        inject(function (_$controller_, _$rootScope_, _$log_, _actrapi_,
                         _AppConfig_, _pcapi_) {
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            $log = _$log_;
            actrapi = _actrapi_;
            AppConfig = _AppConfig_;
            pcapi = _pcapi_;
        });
        scope = $rootScope.$new();
        controller = $controller('IndexController', {$scope: scope});
    });

    describe('Sanity check on dependency injection', function() {
        it('injects the providers we requested', function () {
            [$controller, $rootScope, $log, actrapi, AppConfig,
              pcapi].forEach(function (thing) {
                expect(thing).not.toBeUndefined();
                expect(thing).not.toBeNull();
            });
        });
    });

    /* Main test methods */

    describe('initialize', function() {
        it('shows most accurate school name available');
        it('shows only current terms in dropdown');
        it('excludes ongoing terms in dropdown');
    });
    describe('loadCoursesSummary', function() {
        it('requests course summary with expected data');
        it('makes expected response data available to UI');
    });
    describe('publish', function() {
        it('notifies user when successful');
        it('notifies user when unsuccessful');
        it('creates job with expected data');
        it('turns off operationInProgress when it gets a response');
    });

});
