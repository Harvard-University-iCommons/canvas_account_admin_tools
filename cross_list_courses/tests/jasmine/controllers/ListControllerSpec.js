describe('Unit testing ListController', function () {
    var $controller, $rootScope, $routeParams, courseInstances, $compile, djangoUrl,
        $httpBackend, $window, $log, $uibModal, $sce, $templateCache;

    var controller, scope;

    // set up the test environment
    beforeEach(function () {
        // load the app and the templates-as-module
        module('CourseInfo');
        module('templates');
        inject(function (_$controller_, _$rootScope_, _$routeParams_, _courseInstances_,
                         _$compile_, _djangoUrl_, _$httpBackend_, _$window_, _$log_,
                         _$uibModal_, _$sce_, _$templateCache_) {
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            $routeParams = _$routeParams_;
            courseInstances = _courseInstances_;
            $compile = _$compile_;
            djangoUrl = _djangoUrl_;
            $httpBackend = _$httpBackend_;
            $window = _$window_;
            $log = _$log_;
            $uibModal = _$uibModal_;
            $sce = _$sce_;
            $templateCache = _$templateCache_;

            // this comes from django_auth_lti, just stub it out so that the $httpBackend
            // sanity checks in afterEach() don't fail
            $window.globals = {
                append_resource_link_id: function (url) {
                    return url;
                }
            };
        });
        scope = $rootScope.$new();
    });

    afterEach(function () {
        // sanity checks to make sure no http calls are still pending
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    // DI sanity check
    it('should inject the providers we requested', function () {
        [$controller, $rootScope, $routeParams, courseInstances, $compile,
            djangoUrl, $httpBackend, $window, $log, $sce, $templateCache].forEach(function (thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

});
