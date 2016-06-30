describe('Unit testing people_tool CoursesController', function() {
    var $controller, $rootScope, $routeParams, $compile, djangoUrl,
        $httpBackend, $log, $templateCache, $timeout, $window;
    var controller, scope;

    // set up the test environment
    beforeEach(function() {
        // load in the app and the templates-as-module
        module('PeopleTool');
        module('templates');
        inject(function(_$controller_, _$rootScope_, _$routeParams_,
                        _$compile_, _djangoUrl_, _$httpBackend_, _$log_,
                        _$templateCache_, _$timeout_, _$window_) {
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            $routeParams = _$routeParams_;
            $compile = _$compile_;
            djangoUrl = _djangoUrl_;
            $httpBackend = _$httpBackend_;
            $templateCache = _$templateCache_;
            $timeout = _$timeout_;
            $log = _$log_;
            $window = _$window_;

            // this comes from django_auth_lti, just stub it out so that the
            // $httpBackend sanity checks in afterEach() don't fail
            $window.globals = {
                append_resource_link_id: function(url) { return url; },
            };
        });
        scope = $rootScope.$new();
        controller = $controller('CoursesController', {$scope: scope});
    });

    afterEach(function() {
        // sanity checks to make sure no http calls are still pending
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    // DI sanity check
    it('should inject the providers we requested', function() {
        [$controller, $rootScope, $routeParams, $compile, djangoUrl,
            $httpBackend, $log, $templateCache, $window].forEach(function(thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    describe('dtOptions.ajax', function() {
        it('sends expected GET params to backend');

        it('updates scope with no error message when backend returns no error');

        it('updates scope error message when backend returns error');
    });

    describe('getCourseDescription', function() {
        it('returns short title of title is null');
        it('returns default text if title and short title are both null')

    });

    describe('toggleOperationInProgress', function() {
        it('turns off data table and notes operation in progress when ' +
                'toggled ON');
        it('turns on data table and notes operation not in progress when ' +
                'toggled OFF');
    });

});
