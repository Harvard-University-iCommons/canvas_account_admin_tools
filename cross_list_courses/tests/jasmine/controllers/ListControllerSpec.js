describe('Unit testing ListController', function () {
    var $controller, $rootScope, $httpBackend, $timeout, $document, $window,
        $compile, djangoUrl, $log, $q, $uibModal;

    var controller, scope;
    var xlistURL =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fxlist_maps%2F';

    /* Helpers */

    function clearTemplateFetch() {
        $httpBackend.expectGET("partials/list.html").respond(200, '');
        $httpBackend.flush(1);
    }
    function runTimeout() {
        // use this when logic is wrapped in a timeout so it will be kicked off
        // (immediately) in the next digest cycle
        $timeout.flush();
        $timeout.verifyNoPendingTasks();
    }
    function setupController() {
        controller = $controller('ListController', {$scope: scope});
        // initial call to search() interacts with the dtInstance, so mock it
        // right away for all tests
        scope.dtInstance = jasmine.createSpyObj('dtInstance', ['reloadData']);
        // ignore the initial template loading
        clearTemplateFetch();
        runTimeout();  // so that initial search() is processed
        // emulate a successful datatable reloadData()
        // todo: we should probably implement progress tracking as a queue
        // so it's easier to track complex, overlapping calls to backend
        scope.operationInProgress = false;
    }

    /* Setup, teardown, sanity checks */

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
    // sanity checks
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

    /* Main test methods */

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
            for (var modalScope = scope.$$nextSibling;
                 modalScope != null; modalScope = modalScope.$$nextSibling) {
                if (modalScope.modalOptions.scope.hasOwnProperty('primary')  &&
                        modalScope.modalOptions.scope.hasOwnProperty('secondary')) {
                    break;
                }
            }
            expect(modalScope).not.toBeNull();
            expect(modalScope.modalOptions.scope.primary)
                .toEqual(xlistMap.primary_course_instance.course_instance_id);
            expect(modalScope.modalOptions.scope.secondary)
                .toEqual(xlistMap.secondary_course_instance.course_instance_id);
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
            spyOn(scope, 'deleteCrosslisting').and
                .returnValue(deleteCrosslistingDeferred.promise);
            spyOn(scope, 'handleAjaxErrorResponse');
            spyOn(scope, 'setOperationInProgress');
        });

        it('calls deleteCrosslisting with the correct id', function() {
            scope.removeCrosslisting(1, 2, 3);
            expect(scope.deleteCrosslisting).toHaveBeenCalledWith(1);
        });

        it('shows failure message and reloads even on failure', function() {
            scope.removeCrosslisting(1, 1, 2);

            expect(scope.setOperationInProgress).toHaveBeenCalledWith('remove');
            expect(scope.message).toBe(null);

            deleteCrosslistingDeferred.reject('failure!');
            scope.$digest();

            // cleanup performed dtInstance.reloadData()
            expect(scope.dtInstance.reloadData).toHaveBeenCalled();

            expect(scope.handleAjaxErrorResponse).toHaveBeenCalled();
            expect(scope.message.alertType).toBe('danger');
        });

        it('shows success message and reloads on success', function() {
            scope.removeCrosslisting(1, 1, 2);

            expect(scope.setOperationInProgress).toHaveBeenCalledWith('remove');
            expect(scope.message).toBe(null);

            deleteCrosslistingDeferred.resolve('success!');
            scope.$digest();

            // cleanup performed dtInstance.reloadData()
            expect(scope.dtInstance.reloadData).toHaveBeenCalled();

            expect(scope.handleAjaxErrorResponse).not.toHaveBeenCalled();
            expect(scope.message.alertType).toBe('success');
        });

    });

    describe('search', function() {
        // the actual search params are handled elsewhere on the scope,
        // and included in the query params during the datatable reloadData()
        // so not tested here
        beforeEach(function () {
            spyOn(scope, 'clearMessages');
            spyOn(scope, 'setOperationInProgress');
            expect(scope.operationInProgress).toBe(false);
            // reloadData was already called by search() when controller was
            // initialized, so reset it to track this new invocation of search()
            scope.dtInstance.reloadData.calls.reset();
            scope.search();
        });
        it('kicks off datatable reload and notes operation in progress', function() {
            expect(scope.clearMessages).toHaveBeenCalled();
            expect(scope.setOperationInProgress).toHaveBeenCalledWith('search');
            runTimeout();
            expect(scope.dtInstance.reloadData).toHaveBeenCalled();
        });
    });

    describe('setOperationInProgress', function() {
        beforeEach(function () {
            expect(scope.operationInProgress).toBe(false);
            spyOn(scope, 'setDataTableInteraction');
        });
        it('turns off data table and notes operation in progress when ' +
                'set to a truthy value', function() {
            scope.setOperationInProgress('doSomething');
            runTimeout();
            expect(scope.operationInProgress).toBe('doSomething');
            expect(scope.setDataTableInteraction).toHaveBeenCalledWith(false);
        });

        it('turns on data table and notes operation not in progress when ' +
                'set to a falsy value', function() {
            scope.setOperationInProgress('');
            runTimeout();
            expect(scope.operationInProgress).toBe('');
            expect(scope.setDataTableInteraction).toHaveBeenCalledWith(true);
        });
    });

    xdescribe('setDataTableInteraction', function() {
        // this is heavily DOM-dependent, so skipping for now
    });

    describe('submitAddCrosslisting', function() {
        var primary = '124',
            secondary = '456',
            postNewCrosslistingDeferred = null;

        beforeEach(function () {
            postNewCrosslistingDeferred = $q.defer();
            scope.dtInstance = jasmine.createSpyObj('dtInstance', ['reloadData']);
            spyOn(scope, 'postNewCrosslisting').and
                .returnValue(postNewCrosslistingDeferred.promise);
            spyOn(scope, 'handleAjaxErrorResponse');
            spyOn(scope, 'setOperationInProgress');
            scope.rawFormInput.primary = primary;
            scope.rawFormInput.secondary = secondary;

            scope.submitAddCrosslisting();

            expect(scope.setOperationInProgress).toHaveBeenCalledWith('add');
            expect(scope.message).toBe(null);
        });

        it('should make sure the postNewCrosslisting is called with the ' +
           'correct values', function(){
            expect(scope.postNewCrosslisting)
                .toHaveBeenCalledWith(primary, secondary);
        });

        it('shows correct scope.message on success and reloads datatable',
           function(){
            postNewCrosslistingDeferred.resolve('success!');
            scope.$digest();

            expect(scope.dtInstance.reloadData).toHaveBeenCalled();
            expect(scope.handleAjaxErrorResponse).not.toHaveBeenCalled();
            expect(scope.message.alertType).toBe('success');
        });

        it('shows correct scope.message on failure and cleans up without ' +
           'reloading datatable', function(){
            postNewCrosslistingDeferred.reject('failure!');
            scope.$digest();

            expect(scope.setOperationInProgress).toHaveBeenCalledWith(false);
            expect(scope.dtInstance.reloadData).not.toHaveBeenCalled();
            expect(scope.handleAjaxErrorResponse).toHaveBeenCalled();
            expect(scope.message.alertType).toBe('danger');
        });

        it('shows something friendlier than the default DRF error when ' +
           'already cross-listed, and cleans up without reloading datatable',
           function(){
            var alreadyXlistedResponse = {
                data: {non_field_errors:['unique set']},
                status: 400
            };

            postNewCrosslistingDeferred.reject(alreadyXlistedResponse);
            scope.$digest();

            expect(scope.setOperationInProgress).toHaveBeenCalledWith(false);
            expect(scope.dtInstance.reloadData).not.toHaveBeenCalled();
            expect(scope.handleAjaxErrorResponse).toHaveBeenCalled();
            expect(scope.message.alertType).toBe('danger');
            expect(scope.message.text).toContain('already crosslisted');
        });

    });

});
