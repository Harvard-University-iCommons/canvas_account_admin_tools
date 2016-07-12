describe('Unit testing people_tool SearchController', function() {
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
        controller = $controller('SearchController', {$scope: scope});
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

    describe('searchPeople', function () {
        beforeEach(function() {
            scope.dtInstance = jasmine.createSpyObj('dtInstance', ['reloadData']);
        });

        function repeatCharacter(char, times) {
            // note that `char` appears n-1 times where n is size of array, so
            // array size needs to be one larger than number of characters
            // requested by times
            return new Array(times+1).join(char);
        }

        it('does not hit backend if search string is too long', function() {
            scope.searchTypeOptions.forEach(function(searchTypeOption) {
                scope.messages = [];
                scope.searchType = searchTypeOption;
                scope.queryString = repeatCharacter('a',
                    searchTypeOption.maxLength + 1);
                scope.searchPeople();
                expect($timeout.flush).toThrowError(
                    'No deferred tasks to be flushed');
                expect(scope.dtInstance.reloadData).not.toHaveBeenCalled();
                expect(scope.messages.length).toBe(1);
                expect(scope.messages[0].type).toEqual('warning');
                expect(scope.messages[0].text).toContain(
                    'search term cannot be greater than '
                    + searchTypeOption.maxLength);
            });
        });
        it('triggers backend call (datatable reload) if it meets validation', function() {
            scope.searchTypeOptions.forEach(function(searchTypeOption) {
                scope.searchType = searchTypeOption;
                scope.queryString = repeatCharacter('a',
                    searchTypeOption.maxLength);
                scope.searchPeople();
                $timeout.flush();
                expect(scope.dtInstance.reloadData).toHaveBeenCalled();
                expect(scope.messages).toEqual([]);
                scope.dtInstance.reloadData.calls.reset();
            });
        });
    });

    describe('dtOptions.ajax', function() {
        var ajaxSpy, callbackSpy, digestSpy, logSpy,
            toggleOperationInProgressSpy;
        var data = {start: 0, length: 10,
                    order: [{dir: 'asc', column: 0}]};
        var queryString = 'search term';
        var queryParams = {
            include: 'id_type',
            offset: data.start,
            limit: data.length,
            ordering: 'name_last',  // column 0
            univ_id: queryString
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
            data: [{univ_id: '123'}]
        };
        var fakeAjaxResponseEmpty = {
            recordsTotal: 0,
            recordsFiltered: 0,
            data: []
        };

        var respondWithData = function() {
            var d = $.Deferred();
            d.resolve({count: 1, results:[{univ_id: '123'}]});
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

            scope.messages = ['should be cleared!'];
            scope.queryString = queryString;
            expectedAjaxParams.url = djangoUrl.reverse(
                'icommons_rest_api_proxy', ['api/course/v2/people/']);

            // checks for finally()
            toggleOperationInProgressSpy = spyOn(scope, 'toggleOperationInProgress');
            digestSpy = spyOn(scope, '$digest');
        });

        afterEach(function() {
            expect(toggleOperationInProgressSpy).toHaveBeenCalledWith(false);
            expect(digestSpy).toHaveBeenCalledTimes(1);
        });

        it('sends expected GET params to backend', function() {
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
    describe('toggleOperationInProgress', function() {
        it('turns off data table and notes operation in progress when ' +
                'toggled ON', function() {
            spyOn(scope, 'toggleDataTableInteraction');
            scope.toggleOperationInProgress(true);
            $timeout.flush();  // resolves $timeout
            expect(scope.toggleDataTableInteraction).toHaveBeenCalledWith(false);
        });
        it('turns on data table and notes operation not in progress when ' +
                'toggled OFF', function() {
            spyOn(scope, 'toggleDataTableInteraction');
            scope.toggleOperationInProgress(false);
            $timeout.flush();  // resolves $timeout
            expect(scope.toggleDataTableInteraction).toHaveBeenCalledWith(true);
        });
    });
});
