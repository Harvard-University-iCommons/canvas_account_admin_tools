describe('Unit testing ListController', function () {
    var $controller, $rootScope, $routeParams, $compile, djangoUrl,
        $httpBackend, $window, $log, $uibModal, $sce, $templateCache;

    var controller, scope;
    var xlistURL =
       '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
       '=api%2Fcourse%2Fv2%2Fxlist_maps%2F';

    function clearInitialxlistFetch() {
    //    // handle the initial course instance get
        $httpBackend.expectGET("partials/list.html").respond(200, '');
        $httpBackend.flush(1);
    }

    function setupController() {
        controller = $controller('ListController', {$scope: scope});
        clearInitialxlistFetch();
    }

    // set up the test environment
    beforeEach(function () {
        // load the app and the templates-as-module
        module('CrossListCourses');
        module('templates');
        inject(function (_$controller_, _$rootScope_, _$routeParams_,
                         _$compile_, _djangoUrl_, _$httpBackend_, _$window_, _$log_,
                         _$uibModal_, _$sce_, _$templateCache_) {

            $controller = _$controller_;
            $rootScope = _$rootScope_;
            $routeParams = _$routeParams_;
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
        setupController();
    });

    afterEach(function () {
        // sanity checks to make sure no http calls are still pending
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    // DI sanity check
    it('should inject the providers we requested', function () {
        [$controller, $rootScope, $routeParams, $compile,
            djangoUrl, $httpBackend, $window, $log, $sce, $templateCache].forEach(function (thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    xdescribe('confirmRemove', function() {

        //beforeEach(setupController);

        it('should show the modal dialog when the user clicks delete', function(){
            $httpBackend.expectGET("partials/remove-xlist-map-confirmation.html")
                    .respond(200, {});
                $httpBackend.flush(1);
            var xlistMap = {
                xlist_map_id: 1,
                primary_course_instance: {
                    course_instance_id: 123456
                },
                secondary_course_instance: {
                    course_instance_id: 345678
                }
            };
            scope.confirmRemove(xlistMap);
            scope.$digest();
            var modalScope;
            for (modalScope = scope.$$nextSibling;
                    modalScope != null; modalScope = modalScope.$$nextSibling) {
                if (modalScope.hasOwnProperty('numPeople')  &&
                        modalScope.hasOwnProperty('selectedRoleName')) {
                    break;
                }
            }
            expect(modalScope).not.toBeNull();
        });

    });


    describe('deleteCrosslisting', function() {
        it('should make sure the correct url is called', function(){
            var xlistMapId = 123,
                deleteURL = xlistURL + xlistMapId + '%2F';

            scope.deleteCrosslisting(xlistMapId);

            $httpBackend.expectDELETE(deleteURL).respond(204, {});
            $httpBackend.flush(1);
        });

    });

    xdescribe('formatCourse', function() {

        beforeEach(function () {
        });

        it('should make sure the course text is formatted correctly');

    });


    xdescribe('invalidInput', function() {

        beforeEach(function () {
        });

        it('should return true when valid input is supplied');

        it('should return false when invalid input is supplied');

    });

    xdescribe('isValidCourseInstance', function() {

        beforeEach(function () {
        });

        it('should return true when valid course instance is supplied');

        it('should return false when invalid course instance is supplied');

    });

    xdescribe('postNewCrosslisting', function() {

        beforeEach(function () {
        });

        it('should make sure the post was called with the correct params');

    });


    xdescribe('removeCrosslisting', function() {

        beforeEach(function () {
        });

        it('should make sure the deleteCrosslisting is called with the correct id');
        it('should make sure the scope.message has the correct messag eon failure');

    });


    xdescribe('submitAddCrosslisting', function() {

        beforeEach(function () {
        });

        it('should make sure the postNewCrosslisting is called with the correct values');
        it('should make sure the scope.message has the correct messag eon failure');

    });

});
