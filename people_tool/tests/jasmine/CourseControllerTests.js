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
                var ajaxSpy, callbackSpy, digestSpy, logSpy,
            toggleOperationInProgressSpy;
        var data = {start: 0, length: 10,
                    order: [{dir: 'asc', column: 0}]};

        var course_data = {
            description: 'Untitled Course',
            year: '',
            term: '',
            term_code: '',
            section: '',
            sites: [ { external_id: 'https://coursesite.com'} ],
            code: '',
            school: '',
            cid: undefined,
            xlist_status: '' };

        var queryParams = {
            offset: data.start,
            limit: data.length,
            ordering: 'course__school_id'  // column 0
        };

        var expectedAjaxParams = {
            url: null,  // needs to be added after controller is instantiated
            method: 'GET',
            data: queryParams,
            dataSrc: 'data',
            dataType: 'json'
        };
        var fakeAjaxResponse = {
            recordsTotal: 1,
            recordsFiltered: 1,
            data: [course_data]
        };
        var fakeAjaxResponseEmpty = {
            recordsTotal: 0,
            recordsFiltered: 0,
            data: []
        };

        var respondWithData = function() {
            var d = $.Deferred();
            d.resolve({count: 1, results:[course_data]});
            return d.promise();
        };

        var respondWithError = function() {
            var d = $.Deferred();
            d.reject(undefined, 'textStatus', 'errorThrown');
            return d.promise();
        };

        beforeEach(function() {
            ajaxSpy = spyOn($, 'ajax');
            logSpy = spyOn($log, 'error');
            callbackSpy = jasmine.createSpy('callback');  // datatables callback
            scope.personCoursesUrl = 'api/course/v2/people/12345/course_instances/';
            scope.messages = ['should be cleared!'];
            expectedAjaxParams.url = djangoUrl.reverse(
                'icommons_rest_api_proxy', ['api/course/v2/people/12345/course_instances/']);

            // checks for finally()
            toggleOperationInProgressSpy = spyOn(scope, 'toggleOperationInProgress');
            digestSpy = spyOn(scope, '$digest');
        });

        afterEach(function() {
            expect(toggleOperationInProgressSpy).toHaveBeenCalledWith(false);
            expect(digestSpy).toHaveBeenCalledTimes(1);
        });

        it('sends expected GET params to backend', function(){
            ajaxSpy.and.callFake(respondWithData);
            scope.dtOptions.ajax(data, callbackSpy);  // `settings` not used
            expect(ajaxSpy).toHaveBeenCalledWith(expectedAjaxParams);
            expect(callbackSpy).toHaveBeenCalledWith(fakeAjaxResponse);
            expect(logSpy).not.toHaveBeenCalled();
        });

        it('updates scope with no error message when backend returns no error', function () {
            ajaxSpy.and.callFake(respondWithData);
            scope.dtOptions.ajax(data, callbackSpy);  // `settings` not used
            expect(scope.messages).toEqual([]);
        });
        
        it('updates scope error message when backend returns error', function() {
            ajaxSpy.and.callFake(respondWithError);
            scope.dtOptions.ajax(data, callbackSpy);  // `settings` not used
            expect(ajaxSpy).toHaveBeenCalledWith(expectedAjaxParams);
            expect(callbackSpy).toHaveBeenCalledWith(fakeAjaxResponseEmpty);
            expect(scope.messages.length).toBe(1);
            expect(scope.messages[0].type).toEqual('danger');
            expect(scope.messages[0].text).toContain('Server error');
            expect(logSpy).toHaveBeenCalled();
            var logErrorFirstCall = logSpy.calls.argsFor(0)[0];
            expect(logErrorFirstCall).toContain(
                'Error getting data from ' + expectedAjaxParams.url);
            expect(logErrorFirstCall).toContain('textStatus');
            expect(logErrorFirstCall).toContain('errorThrown');
        });
    });

    describe('getCourseDescription', function() {
        it('returns short title of title is null', function(){
            var course = {
                title: '',
                short_title: 'this is a short title'
            };
            result = scope.getCourseDescription(course);
            expect(result).toBe('this is a short title');
        });
        it('returns default text if title and short title are both null', function(){
            var course = {
                title: '',
                short_title: ''
            };
            result = scope.getCourseDescription(course);
            expect(result).toBe('Untitled Course');
        });
    });

    describe('toggleOperationInProgress', function() {
        it('turns off data table and notes operation in progress when ' +
                'toggled ON', function(){
            var toggleDataTableInteractionSpy = spyOn(scope, 'toggleDataTableInteraction');
            scope.toggleOperationInProgress(false);
            $timeout.flush();
            $timeout.verifyNoPendingTasks();
            expect(toggleDataTableInteractionSpy).toHaveBeenCalledWith(true);
        });

        it('turns on data table and notes operation not in progress when ' +
                'toggled OFF', function(){
            var toggleDataTableInteractionSpy = spyOn(scope, 'toggleDataTableInteraction');
            scope.toggleOperationInProgress(false);
            $timeout.flush();
            $timeout.verifyNoPendingTasks();
            expect(toggleDataTableInteractionSpy).toHaveBeenCalledWith(true);
        });
    });
});
