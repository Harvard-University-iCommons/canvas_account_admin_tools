describe('Unit testing ListController', function () {
    var $controller, $rootScope, $httpBackend, $timeout, $document, $window,
        $compile, djangoUrl, $log, $q, $uibModal;

    var controller, scope;
    var xlistURL =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fxlist_maps%2F';


    function clearInitialxlistFetch() {
        // handle the initial course instance get
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
        inject(function (_$controller_, _$rootScope_, _$httpBackend_,
                         _$timeout_, _$document_, _$window_, _$compile_,
                         _djangoUrl_, _$log_, _$q_, _$uibModal_) {

            $controller = _$controller_;
            $rootScope = _$rootScope_;
            $httpBackend = _$httpBackend_;
            $timeout = _$timeout_;
            $document = _$document_;
            $window = _$window_;
            $compile = _$compile_;
            djangoUrl = _djangoUrl_;
            $log = _$log_;
            $q = _$q_;
            $uibModal = _$uibModal_;

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
        [$controller, $rootScope, $timeout, $document, $window, $compile,
            djangoUrl, $log, $q].forEach(function (thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    describe('confirmRemove', function() {
        var xlistMap = {
            xlist_map_id: 1,
            primary_course_instance: {
                course_instance_id: 123456
            },
            secondary_course_instance: {
                course_instance_id: 345678
            }
        };
        beforeEach(function(){
            spyOn(scope, 'clearMessages');
            spyOn(scope, 'removeCrosslisting');
            scope.confirmRemove(xlistMap);
            $httpBackend.expectGET("partials/remove-xlist-map-confirmation.html").respond(200, '');
            $httpBackend.flush(1);
            scope.$digest();
        });
        it('should show the modal dialog with correct data when the user clicks delete', function(){
            for (modalScope = scope.$$nextSibling; modalScope != null; modalScope = modalScope.$$nextSibling) {
                if (modalScope.modalOptions.scope.hasOwnProperty('primary')  &&
                        modalScope.modalOptions.scope.hasOwnProperty('secondary')) {
                    break;
                }
            }
            expect(modalScope).not.toBeNull();
            expect(modalScope.modalOptions.scope.primary).toEqual(xlistMap.primary_course_instance.course_instance_id);
            expect(modalScope.modalOptions.scope.secondary).toEqual(xlistMap.secondary_course_instance.course_instance_id);
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

    describe('formatCourse', function() {
        it('should make sure the course text is formatted correctly', function() {
            var courseInstance = {
                "course": {
                    "registrar_code": "24259",
                    "school_id": "ext"
                },
                "course_instance_id": 338920,
                "term": {
                    "display_name": "Spring 2017"
                }
            };
            var result = scope.formatCourse(courseInstance);
            expect(result).toBe('EXT 24259-Spring 2017-338920');
        });
    });

    describe('invalidInput', function() {
        it('indicates validity when valid input is supplied', function() {
            // both course instances are valid
            spyOn(scope, 'isValidCourseInstance').and.returnValue(true);
            // different course instances (identical ones cannot be paired)
            spyOn(scope, 'cleanCourseInstanceInput').and
                .returnValues('123', '456');

            expect(scope.invalidInput()).toBe(false);
        });

        it('indicates invalid when primary is invalid', function() {
            spyOn(scope, 'isValidCourseInstance').and.returnValues(false, true);
            // different course instances (identical ones cannot be paired)
            spyOn(scope, 'cleanCourseInstanceInput').and
                .returnValues('123', '456');
            expect(scope.invalidInput()).toBe(true);
        });
        it('indicates invalid when secondary is invalid', function() {
            spyOn(scope, 'isValidCourseInstance').and.returnValues(true, false);
            // different course instances (identical ones cannot be paired)
            spyOn(scope, 'cleanCourseInstanceInput').and.returnValues('123', '456');
            expect(scope.invalidInput()).toBe(true);
        });

        it('indicates invalid when primary and secondary match', function() {
            // both course instances are valid
            spyOn(scope, 'isValidCourseInstance').and.returnValue(true);
            // identical course instance ids cannot be paired
            spyOn(scope, 'cleanCourseInstanceInput').and.returnValue('123');
            expect(scope.invalidInput()).toBe(true);
        });
    });

    describe('isValidCourseInstance', function() {
        beforeEach(function () {
            spyOn(scope, 'cleanCourseInstanceInput').and.callFake(
                function(input) { return input; });
        });

        it('returns true when valid course instance is supplied', function() {
            expect(scope.isValidCourseInstance('1234567')).toBe(true);
            expect(scope.isValidCourseInstance('1')).toBe(true);
        });

        it('returns false when invalid course instance is supplied', function() {
            expect(scope.isValidCourseInstance('123 4567')).toBe(false);
            expect(scope.isValidCourseInstance('abc123')).toBe(false);
            expect(scope.isValidCourseInstance('')).toBe(false);
        });
    });

    describe('postNewCrosslisting', function() {
        it('calls post with the correct params', function() {
            var result = null,
                primary = 123,
                secondary = 456,
                expectedPostParams = {
                    primary_course_instance: primary,
                    secondary_course_instance: secondary
                },
                expectedResponse = {
                    status: 201  // format is unimportant for purposes of test
                };


            scope.postNewCrosslisting(primary, secondary)
                .then(function(response) { result = response.data; });

            $httpBackend.expectPOST(xlistURL, expectedPostParams)
                .respond(201, expectedResponse);
            $httpBackend.flush(1);

            // resolve promise
            scope.$digest();

            expect(result).toEqual(expectedResponse);
        });
    });

    describe('removeCrosslisting', function() {
        var deleteCrosslistingDeferred = null;

        beforeEach(function () {
            deleteCrosslistingDeferred = $q.defer();
            scope.dtInstance = jasmine.createSpyObj('dtInstance', ['reloadData']);
            spyOn(scope, 'deleteCrosslisting').and
                .returnValue(deleteCrosslistingDeferred.promise);
            spyOn(scope, 'handleAjaxErrorResponse');
        });

        it('calls deleteCrosslisting with the correct id', function() {
            scope.removeCrosslisting(1, 2, 3);
            expect(scope.deleteCrosslisting).toHaveBeenCalledWith(1);
        });

        it('shows failure message and cleans up on failure', function() {
            scope.removeCrosslisting(1, 1, 2);

            expect(scope.operationInProgress).toBe('remove');
            expect(scope.message).toBe(null);

            deleteCrosslistingDeferred.reject('failure!');
            scope.$digest();

            expect(scope.operationInProgress).toBeNull();
            expect(scope.dtInstance.reloadData).toHaveBeenCalled();
            expect(scope.handleAjaxErrorResponse).toHaveBeenCalled();
            expect(scope.message.alertType).toBe('danger');
        });

        it('shows success message and cleans up on success', function() {
            scope.removeCrosslisting(1, 1, 2);

            expect(scope.operationInProgress).toBe('remove');
            expect(scope.message).toBe(null);

            deleteCrosslistingDeferred.resolve('success!');
            scope.$digest();

            expect(scope.operationInProgress).toBeNull();
            expect(scope.dtInstance.reloadData).toHaveBeenCalled();
            expect(scope.handleAjaxErrorResponse).not.toHaveBeenCalled();
            expect(scope.message.alertType).toBe('success');
        });

    });

    describe('submitAddCrosslisting', function() {
        var primary = '124',
            secondary = '456',
            expectedPostParams = {
                    primary_course_instance: primary,
                    secondary_course_instance: secondary
            },
            expectedResponse = {
                    status: 201  // format is unimportant for purposes of test
            },
            expectedFailureResponse = {
                alertType: 'danger',
                text: primary+' could not be crosslisted with '+secondary+' at this time. Please check the course instance IDs and try again.'
            };
        beforeEach(function () {
            scope.rawFormInput.primary = primary;
            scope.rawFormInput.secondary = secondary;
            scope.dtInstance = {reloadData: function(){}};
            scope.submitAddCrosslisting();
        });

        it('should make sure the postNewCrosslisting is called with the correct values', function(){
            $httpBackend.expectPOST(xlistURL, expectedPostParams)
                .respond(201, expectedResponse);
            $httpBackend.flush(1);
            expect(scope.message).toEqual({alertType: 'success', text: '124 was successfully crosslisted with 456.'});
        });

        it('should make sure the scope.message has the correct messag eon failure', function(){
            $httpBackend.expectPOST(xlistURL, expectedPostParams)
                .respond(400, expectedResponse);
            $httpBackend.flush(1);
            expect(scope.message).toEqual(expectedFailureResponse);
        });

    });

});
