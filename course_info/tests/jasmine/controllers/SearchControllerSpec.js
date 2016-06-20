// NOTE - this is still a work in progress, doesn't really test anything useful

describe('Unit testing SearchController', function() {
    beforeEach(module('CourseInfo'));
    beforeEach(module('templates'));

    var $controller, $window, $document, $httpBackend, $rootScope, $templateCache;
    var scope, controller;

    beforeEach(inject(function(_$controller_, _$window_, _$document_, 
                               _$httpBackend_, _$rootScope_, _$templateCache_) {
        // The injector unwraps the underscores (_) from around
        // the parameter names when matching
        $controller = _$controller_;
        $window = _$window_;
        $document = _$document_;
        $httpBackend = _$httpBackend_;
        $rootScope = _$rootScope_;
        $templateCache = _$templateCache_;

        // this comes from django_auth_lti, just stub it out so that the $httpBackend
        // sanity checks in afterEach() don't fail
        $window.globals = {
            append_resource_link_id: function(url) { return url; },
        };

        // instantiate the controller, give it a $scope
        scope = $rootScope.$new();
        controller = $controller('SearchController', { $scope: scope });

        // always expect the controller constructor to call for term codes
        var term_codes = {
            results: [
                {
                    term_code: 0,
                    term_name: 'Summer',
                    sort_order: 40
                },
                {
                    term_code: 1,
                    term_name: 'Fall',
                    sort_order: 60
                },
                {
                    term_code: 2,
                    term_name: 'Spring',
                    sort_order: 30
                },
            ],
            next: '',
        };
        $httpBackend.expectGET('/icommons_rest_api/api/course/v2/term_codes/?limit=100')
            .respond(200, JSON.stringify(term_codes));
        $httpBackend.flush(1); // flush the term_codes request
    }));

    it("should inject the providers we've requested", function() {
        [$controller, $window, $document, $httpBackend, $rootScope].forEach(function(thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    it("should instantiate the controller", function() {
        expect(controller).not.toBe(null);
    });

    afterEach(function() {
        // sanity checks to make sure no http work is still pending
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    describe('$scope setup', function() {

    });

    describe('$scope.enableColumnSorting()', function() {

    });

    describe('$scope.courseInstanceToTable()', function() {

    });

    describe('$scope.initializeDatatable()', function() {

    });

    describe('$scope.searchCourseInstances()', function() {

    });

    describe('getCourseDescription()', function() {
        it('should display the course title if title is present', function () {
            var course = { title: 'ABC'};
            result = scope.getCourseDescription(course);
            expect(result).toEqual('ABC');
        });

        it('should dipslay the course short title if title is not present and short title is', function() {
            var course = { title: '', short_title: 'short'};
            result = scope.getCourseDescription(course);
            expect(result).toEqual('short');
        });

        it('should display Untitled Course when no title or short title are present', function(){
            var course = { title: '', short_title: ''};
            result = scope.getCourseDescription(course);
            expect(result).toEqual('Untitled Course');
        });

        it('should display Untitled Course when no data is present', function(){
            var course = {};
            result = scope.getCourseDescription(course);
            expect(result).toEqual('Untitled Course');
        });
        
        it('should display title if both title and short title are present', function(){
            var course = { title: 'ABC', short_title: 'short'};
            result = scope.getCourseDescription(course);
            expect(result).toEqual('ABC');
        });
    });
});
