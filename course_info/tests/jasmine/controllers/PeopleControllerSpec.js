// Regex taken from Errata #2624 (https://www.rfc-editor.org/errata_search.php?rfc=3986),
// filed against RFC 3986 (https://www.rfc-editor.org/info/rfc3986) Appendix B
// The RFC appendix explains the different capture groups.  The query string is $7.
var URIRegex = /^(([^:\/?#]+):)?(\/\/([^\/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?/;
function getParametersFromURI(uri) {
    var URIComponents = URIRegex.exec(decodeURI(uri));
    var paramStrings = URIComponents[7].split('&');
    var params = {};
    paramStrings.forEach(function(paramString) {
        var kv = paramString.split('=');
        params[kv[0]] = kv[1];
    });
    return params;
}

// needed to let angular expect a url where the parameter order may vary
// (as urls created by djangoUrl in the controller do).
function validateURIHasParameters(uri, params) {
    var actualParams = getParametersFromURI(uri);
    for (var key in params) {
        if (actualParams[key] !== params[key]) {
            return false;
        }
    }
    return true;
}

describe('Unit testing PeopleController', function() {
    var $controller, $rootScope, $routeParams, courseInstances, $compile, djangoUrl,
        $httpBackend, $window, $log, $uibModal, $templateCache, angularDRF, $q;
    var controller, scope;
    var courseInstanceId = 1234567890;
    var courseInstanceURL =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fcourse_instances%2F' + courseInstanceId + '%2F';
    var coursePeopleURL = courseInstanceURL + 'people%2F';

    // helper methods for DRYer code
    function clearInitialCourseInstanceFetch() {
        // handle the initial course instance get
        $httpBackend.expectGET(courseInstanceURL).respond(200, '');
        $httpBackend.flush(1);
    }

    // set up the test environment
    beforeEach(function() {
        // load in the app and the templates-as-module
        module('CourseInfo');
        module('templates');
        inject(function(_$controller_, _$rootScope_, _$routeParams_, _courseInstances_,
                        _$compile_, _djangoUrl_, _$httpBackend_, _$window_, _$log_,
                        _$uibModal_, _$templateCache_, _angularDRF_, _$q_) {
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
            $templateCache = _$templateCache_;
            angularDRF = _angularDRF_;
            $q = _$q_;

            // this comes from django_auth_lti, just stub it out so that the $httpBackend
            // sanity checks in afterEach() don't fail
            $window.globals = {
                append_resource_link_id: function(url) { return url; },
            };
        });
        scope = $rootScope.$new();
        $routeParams.courseInstanceId = courseInstanceId;
    });

    afterEach(function() {
        // sanity checks to make sure no http calls are still pending
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    // DI sanity check
    it('should inject the providers we requested', function() {
        [$controller, $rootScope, $routeParams, courseInstances, $compile,
         djangoUrl, $httpBackend, $window, $log, $uibModal, $templateCache,
         angularDRF, $q].forEach(function(thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    // todo: these need to be checked and moved into alphabetical position in the test file
    describe('addPeopleToCourse', function() {
        it('will add people as soon as their lookup is complete without ' +
            'waiting on all people lookups to complete');
        it('won\'t attempt to add anyone until course membership is available');
        it('won\'t bother waiting for profile lookups or POSTing new members ' +
            'if course membership lookup fails');
    });

    describe('addNewMember', function() {

        var personResult = [];
        var members = {};

        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope });
            //var members = {};
            members["12345678"] = [{
                        active: 1,
                        email_address: "test45@mcelroy.org",
                        name_first: "Test",
                        name_last: "User",
                        prime_role_indicator: "Y",
                        role_type_cd: "STUDENT",
                        univ_id: "12345678"
                    }];
            members["43215678"] = [{
                        active: 1,
                        email_address: "test46@mcelroy.org",
                        name_first: "Peter",
                        name_last: "Smith",
                        prime_role_indicator: "Y",
                        role_type_cd: "STUDENT",
                        univ_id: "43215678"
                    }];

            personResult.push(
                {
                    active: 1,
                    email_address: "test45@mcelroy.org",
                    name_first: "Test",
                    name_last: "User",
                    prime_role_indicator: "Y",
                    role_type_cd: "STUDENT",
                    univ_id: "12345678"
                },
                ["test45@mcelroy.org"]
            );
        });
        afterEach(function() {
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.flush(1);
        });
        it('won\'t add person if they already have a course enrollment', function(){
            spyOn(scope, 'filterSearchResults').and.returnValue([personResult[0]]);
            spyOn(scope, 'getProfileFullName').and.returnValue('Test User');
            spyOn(scope, 'addNewMemberToCourse').and.returnValue({'result': 'success'});
            var result = scope.addNewMember(personResult, members);
            expect(scope.getProfileFullName).toHaveBeenCalledWith(personResult[0]);
            expect(result).toBeNull();
        });
        it('won\'t add if they could not be found via /people lookup', function(){
            var personResult = [{}, ["test45@mcelroy.org"]];
            spyOn(scope, 'filterSearchResults').and.returnValue([]);
            spyOn(scope, 'getProfileFullName').and.returnValue('Test User');
            spyOn(scope, 'addNewMemberToCourse').and.returnValue({'result': 'success'});
            var result = scope.addNewMember(personResult, members);
            expect(scope.messages.warnings).toEqual([{type: 'notFound',
                    searchTerm: personResult[1]}]);
            expect(scope.getProfileFullName).not.toHaveBeenCalled();

            expect(result).toBeNull();
        });
        it('won\'t add if multiple profiles returned by /people lookup', function(){
            var secondPerson = {
                    active: 1,
                    email_address: "test48@mcelroy.org",
                    name_first: "Test",
                    name_last: "User2",
                    prime_role_indicator: "Y",
                    role_type_cd: "STUDENT",
                    univ_id: "12345675"
                };
            spyOn(scope, 'filterSearchResults').and.returnValue([personResult[0], secondPerson]);
            spyOn(scope, 'getProfileFullName').and.returnValue('Test User');
            spyOn(scope, 'addNewMemberToCourse').and.returnValue({'result': 'success'});
            var result = scope.addNewMember(personResult, members);
            expect(scope.messages.warnings[0].type).toEqual('multipleProfiles');
            expect(scope.getProfileFullName).toHaveBeenCalledWith(personResult[0]);
            expect(result).toBeNull();
        });
        it('adds person if not in course and single profile available', function(){
            var newPerson = [
                {
                    active: 1,
                    email_address: "test49@mcelroy.org",
                    name_first: "Test",
                    name_last: "New User",
                    prime_role_indicator: "Y",
                    role_type_cd: "STUDENT",
                    univ_id: '12345674'
                },
                ["test49@mcelroy.org"]
            ];
            spyOn(scope, 'filterSearchResults').and.returnValue([newPerson[0]]);
            spyOn(scope, 'getProfileFullName').and.returnValue('Test New User');
            spyOn(scope, 'addNewMemberToCourse').and.returnValue({'result': 'success'});
            var result = scope.addNewMember(newPerson, members);
            var postParams = {
                        user_id: '12345674',
                        role_id: 0};
            expect(scope.getProfileFullName).toHaveBeenCalledWith(newPerson[0]);
            expect(scope.addNewMemberToCourse).toHaveBeenCalledWith(postParams, 'Test New User', newPerson[1]);
            expect(result).toEqual({ result: 'success' });
        });
    });
    describe('addNewMemberToCourse', function() {
        var user = {user_id: 'bobdobbs', role_id: 0};
        var userJson = JSON.stringify(user);
        var ajaxResponse;
        var args = {postParams: user, name: 'test user', searchTerm:'123'};

        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope });
            spyOn(scope, 'updateProgressBar');
            clearInitialCourseInstanceFetch();
            scope.addNewMemberToCourse(args.postParams, args.name,
                    args.searchTerm)
                .then(function(response) { ajaxResponse = response; });
        });
        afterEach(function() {
            // should update the progress bar regardless of success/failure
            expect(scope.updateProgressBar).toHaveBeenCalled();
        });

        it('tracks successes', function() {
            $httpBackend.expectPOST(coursePeopleURL, user)
                .respond(201, userJson);
            $httpBackend.flush(1);

            expect(scope.tracking.successes).toEqual(1);
            expect(scope.tracking.failures).toEqual(0);
            expect(scope.messages.warnings).toEqual([]);
            expect(ajaxResponse.status).toEqual(201);
            expect(ajaxResponse.data).toEqual(user);
        });

        describe('failure cases', function() {
            beforeEach(function() {
                spyOn(scope, 'handleAjaxErrorResponse');
            });
            afterEach(function() {
                expect(scope.tracking.successes).toEqual(0);
                expect(scope.tracking.failures).toEqual(1);
                expect(ajaxResponse.status).toEqual(500);
                expect(scope.handleAjaxErrorResponse).toHaveBeenCalled();
            });
            it('tracks non-partial failure, logs appropriate error message, ' +
                'and does not reject promise chain', function() {
                var expectedWarning = {
                    type: 'addFailed', name: args.name, searchTerm: args.searchTerm
                };
                var testFailureData = {detail: 'test failure'};

                $httpBackend.expectPOST(coursePeopleURL, user)
                    .respond(500, testFailureData);
                $httpBackend.flush(1);

                expect(scope.messages.warnings).toEqual([expectedWarning]);
                expect(ajaxResponse.data).toEqual(testFailureData);
            });
            it('tracks partial failure, logs appropriate error message, and ' +
                'does not reject promise chain', function() {
                var testFailureData = {
                    detail: 'Canvas API error details: testing'};
                var expectedWarning = {
                    type: 'partialFailure',
                    failureDetail: testFailureData.detail,
                    name: args.name,
                    searchTerm: args.searchTerm
                };

                $httpBackend.expectPOST(coursePeopleURL, user)
                    .respond(500, testFailureData);
                $httpBackend.flush(1);

                expect(scope.messages.warnings).toEqual([expectedWarning]);
                expect(ajaxResponse.data).toEqual(testFailureData);
            });
        });

    });
    describe('confirmAddPeopleToCourse', function() {
        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope});
            clearInitialCourseInstanceFetch();
            var searchTerm ="123456789, \n987654321";
            spyOn(scope, 'addPeopleToCourse');
            scope.confirmAddPeopleToCourse(searchTerm);
            scope.$digest();  // resolves modal instantiation
        });

        // todo: cannot yet find a way to access the modal's controller scope
        // within a test
        it('reflects the right role and number of people');

        it('initiates the process if confirmed', function() {
            scope.confirmAddModalInstance.close();
            scope.$digest();  // resolves modalInstance result
            expect(scope.addPeopleToCourse).toHaveBeenCalled();
        });

        it('doesn\'t initiate the process if canceled', function() {
            scope.confirmAddModalInstance.dismiss();
            scope.$digest();  // resolves confirmAddModalInstance result
            expect(scope.addPeopleToCourse).not.toHaveBeenCalled();
        });

    });
    describe('getMembersByUserId', function() {
        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope });
        });
        afterEach(function() {
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.flush(1);
        });
        it('maps enrollments to IDs', function() {
            var memberList = [{
                    "role": {
                        "canvas_role": "student",
                        "role_id": 101,
                        "role_name": "Teaching Fellow"
                    },
                    "source": "xmlfeed",
                    "user_id": "12345678",
                    "profile": {
                        "active": 1,
                        "email_address": "smith@harvard.edu",
                        "name_first": "Sarah",
                        "name_last": "Smith",
                        "prime_role_indicator": "Y",
                        "role_type_cd": "STUDENT",
                        "univ_id": "12345678"
                    }
                },
                {
                    "role": {
                        "canvas_role": "student",
                        "role_id": 102,
                        "role_name": "TA"
                    },
                    "source": "xmlfeed",
                    "user_id": "87654321",
                    "profile": {
                        "active": 1,
                        "email_address": "smith@harvard.edu",
                        "name_first": "kid",
                        "name_last": "smart",
                        "prime_role_indicator": "Y",
                        "role_type_cd": "STUDENT",
                        "univ_id": "87654321"
                    }
                }];
            var result = scope.getMembersByUserId(memberList);
            memberList[0].role.role_name = 'TA';
            expect(result).toEqual({12345678: [memberList[0]], 87654321: [memberList[1]]});
        });
    });
    describe('getSearchTermList', function() {
        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope });
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.flush(1);
        });

        it('returns a list of trimmed search terms split on comma and newline', function() {
            var testCases = [
                // [inputString, expectedResults],
                ['123456789', ['123456789']],
                [' 123456789 ', ['123456789']],
                ['123456789,987654321', ['123456789', '987654321']],
                ['123456789   \t,\t\t\t987654321', ['123456789', '987654321']],
                ['123456789\n987654321', ['123456789', '987654321']],
                [' 123456789 \n 987654321 ', ['123456789', '987654321']],
                [' ,123456789, ,\n, ,987654321, ,', ['123456789', '987654321']],
            ];

            testCases.forEach(function(testCase) {
                var inputString = testCase[0];
                var expectedResults = testCase[1];
                expect(scope.getSearchTermList(inputString))
                      .toEqual(expectedResults);
            });
        });
    });
    describe('lookupCourseMembers', function() {
        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope });
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.flush(1);

            // pass through to the $http backend to get a promise
            spyOn(angularDRF, 'get').and.callThrough();
        });

        afterEach(function() {
            // flush the $http backend call that angularURL makes for us.
            // assumes that the angularDRF.get call params were validated,
            // so we don't have to care about the url.
            $httpBackend.expectGET(function(url) { return true; })
                        .respond(200, '');
            $httpBackend.flush(1);
        });

        it('makes the expected call and returns a promise', function() {
            var promise = scope.lookupCourseMembers();

            // verifying the return value has a `then()` method is as close
            // as we get to verify we got back a promise.
            expect(angular.isFunction(promise.then)).toBe(true);

            // ensure the url and some of the params are what we expect
            expect(angularDRF.get).toHaveBeenCalledTimes(1);
            var callArgs = angularDRF.get.calls.argsFor(0);
            expect(callArgs[0]).toEqual(coursePeopleURL);
            expect(callArgs[1].params['-source']).toEqual('xreg_map');
            expect(callArgs[1].drf.hasOwnProperty('pageSize')).toBe(true);
        });
    });
    describe('lookupPeople', function() {
        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope });
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.flush(1);
        });

        it('creates people lookups that are tracked in controller scope on ' +
                'failure', function() {
            // sanity check the scope before calling lookupPeople
            expect(scope.tracking.failures).toEqual(0);
            expect(scope.messages.warnings).toEqual([]);

            // set up the spy to reject
            spyOn(angularDRF, 'get').and.returnValue($q.reject(new Error()));

            // call it, then digest to process the rejection
            var promiseList = scope.lookupPeople(['12345678']);
            scope.$digest();

            // verify that the failures are marked on the scope
            expect(scope.tracking.failures).toEqual(1);
            expect(scope.messages.warnings)
                .toEqual([{type: 'personLookupFailed', searchTerm: '12345678'}]);
        });

        it('creates appropriate person lookups (id or email)', function() {
            var testCases = [
                // [searchTerms, expectedParams]
                [['user@example.edu'], [{email_address: 'user@example.edu'}]],
                [['12345678'], [{univ_id: '12345678'}]],
                [['user@example.edu', '12345678'],
                 [{email_address: 'user@example.edu'}, {univ_id: '12345678'}]],
            ];

            spyOn(angularDRF, 'get').and.returnValue($q.resolve());

            testCases.forEach(function (testCase) {
                var searchTerms = testCase[0];
                var expectedParams = testCase[1];

                var promiseList = scope.lookupPeople(searchTerms);
                expect(promiseList.length).toEqual(searchTerms.length);
                expect(angularDRF.get).toHaveBeenCalledTimes(searchTerms.length);
                for (var i=0; i<expectedParams.length; i++) {
                    var args = angularDRF.get.calls.argsFor(i);
                    expect(args[1].params).toEqual(expectedParams[i]);
                }
                angularDRF.get.calls.reset();
            });
        });
    });
    describe('showAddNewMemberResults', function() {
        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope});
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.flush(1);
        });

        it('reloads datatable only if membership changed', function() {
            scope.tracking.successes = 1;
            scope.tracking.total = 2;
            scope.tracking.failure = 1;

            // mock out the datatable so we can verify that it gets reloaded
            scope.dtInstance = {reloadData: function(){}};
            spyOn(scope.dtInstance, 'reloadData');

            //invoke the method
            scope.showAddNewMemberResults();
            expect(scope.dtInstance.reloadData.calls.count()).toEqual(1);

        });

        it('doesnt reload datatable membership is unchanged', function() {
            scope.tracking.successes = 0;
            scope.tracking.total = 2;
            scope.tracking.failure = 2;

            // mock out the datatable so we can verify that it gets reloaded
            scope.dtInstance = {reloadData: function(){}};
            spyOn(scope.dtInstance, 'reloadData');

            //invoke the method
            scope.showAddNewMemberResults();

            expect(scope.dtInstance.reloadData).not.toHaveBeenCalled();
        });

        it('updates success message based on success/failure counts', function(){
            scope.tracking.total = 2;
            scope.tracking.successes = 2;
            scope.tracking.failure = 0;

            // mock out the datatable so we can verify that it gets reloaded
            scope.dtInstance = {reloadData: function(){}};
            spyOn(scope.dtInstance, 'reloadData');

            //invoke the method
            scope.showAddNewMemberResults();
            expect(scope.messages.success['type']).toEqual('add');
            expect(scope.messages.success['alertType']).toEqual('success');
        });

        it('updates warning message based on success/failure counts', function(){
            scope.tracking.total = 1;
            scope.tracking.successes = 2;
            scope.tracking.failure = 1;

            // mock out the datatable so we can verify that it gets reloaded
            scope.dtInstance = {reloadData: function(){}};
            spyOn(scope.dtInstance, 'reloadData');

            //invoke the method
            scope.showAddNewMemberResults();
            expect(scope.messages.success['type']).toEqual('add');
            expect(scope.messages.success['alertType']).toEqual('warning');
        });

        it('updates danger message based on success/failure counts', function(){

            scope.tracking.total = 2;
            scope.tracking.failure = 2;
            scope.tracking.successes = 0;

            // mock out the datatable so we can verify that it gets reloaded
            scope.dtInstance = {reloadData: function(){}};
            spyOn(scope.dtInstance, 'reloadData');

            //invoke the method
            scope.showAddNewMemberResults();
            expect(scope.messages.success['type']).toEqual('add');
            expect(scope.messages.success['alertType']).toEqual('danger');
        });
    });
    describe('updateProgressBar', function() {
        beforeEach(function () {
            controller = $controller('PeopleController', {$scope: scope});
        });
        afterEach(function () {
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.flush(1);
        });

        it('shows current add person progress based on scope vars', function () {
            scope.tracking.total = 3;
            scope.tracking.successes = 1;
            scope.tracking.failure = 1;
            var expectedMsg = 'Adding 2 of 3'
            //invoke the method
            scope.updateProgressBar();
            expect(scope.messages.progress).toEqual(expectedMsg)
        });

        it('displays override text if provided', function () {
            scope.tracking.total = 3;
            scope.tracking.successes = 1;
            scope.tracking.failure = 1;

            var text = 'Looking up 3 people '
            //invoke the method
            scope.updateProgressBar(text);
            expect(scope.messages.progress).toEqual(text);
        });
    });

    describe('$scope setup', function() {
        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope });
        });

        afterEach(function() {
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.flush(1);
        });

        it('should set the course instance id', function() {
            expect(scope.courseInstanceId).toEqual($routeParams.courseInstanceId);
        });

        it('should have a null dtInstance', function() {
            expect(scope.dtInstance).toBeNull();
        });

        it('should have a bunch of non-null variables set up', function() {
            ['dtColumns', 'dtOptions', 'roles', 'operationInProgress',
                'selectedRole'].forEach(function(scopeAttr) {
                expect(scope[scopeAttr]).not.toBeUndefined();
            });
        });
    });

    describe('setCourseInstance', function() {
        var ci;
        beforeEach(function() {
            // if we want to pull the instance id from $routeParams, this has
            // to be in a beforeEach(), can't be in a describe().
            ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'Test Title',
                course: {
                    school_id: 'abc',
                    registrar_code_display: '2222'
                },
            };
        });

        it('should work when courseInstances has the course instance', function() {
            courseInstances.instances[ci.course_instance_id] = ci;
            controller = $controller('PeopleController', {$scope: scope});
            expect(scope.courseInstance['title']).toEqual(ci.title);
            //check one other additional metadata here  for sanity check
            expect(scope.courseInstance['school']).toEqual
                    (ci.course.school_id.toUpperCase());
        });

        it('should work whenCourseInstances is empty', function() {
            controller = $controller('PeopleController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL)
                        .respond(200, JSON.stringify(ci));
            $httpBackend.flush(1);
            expect(scope.courseInstance['title']).toEqual(ci.title);
            expect(scope.courseInstance['school']).toEqual
                    (ci.course.school_id.toUpperCase());
        });

        it('courseInstance whould not be set when CourseInstance doesnt match', function() {
            //override the course_instance_id for ci
            ci.course_instance_id = '1234'
            controller = $controller('PeopleController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL)
                        .respond(200, JSON.stringify(ci));
            $httpBackend.flush(1);
            expect(scope.courseInstance).not.toBeDefined();
        });
    });

    describe('getFormattedCourseInstance', function() {
        var ci;
        beforeEach(function() {
            ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'Test Title',
                sites: [
                    {
                        external_id: 'https://x.y.z/888',
                        site_id: '888',
                    }
                ],
                course: {
                    school_id: 'abc',
                    registrar_code_display: '4x2',
                    registrar_code: '2222',
                    course_id : '789',
                },
                term: {
                    display_name: 'Summer 2015',
                    academic_year : '2015',
                },
                primary_xlist_instances:[],
            };
        });

        it('formats the course instance data for the UI', function() {
            courseInstances.instances[ci.course_instance_id] = ci;

            controller = $controller('PeopleController', {$scope: scope});

            expect(scope.courseInstance['title']).toEqual(ci.title);
            expect(scope.courseInstance['school']).toEqual
                    (ci.course.school_id.toUpperCase());
            expect(scope.courseInstance['term']).toEqual(ci.term.display_name);
            expect(scope.courseInstance['year']).toEqual(ci.term.academic_year);
            expect(scope.courseInstance['course_instance_id']).toEqual(ci.course_instance_id);
            expect(scope.courseInstance['registrar_code_display']).toEqual(
                    ci.course.registrar_code_display);
            expect(scope.courseInstance['sites']).toEqual('888');
            expect(scope.courseInstance['xlist_status']).toEqual('N/A');
        });
        it('uses registrar_code if registrar_code_display is blank', function() {
            courseInstances.instances[ci.course_instance_id] = angular.copy(ci);
            courseInstances.instances[ci.course_instance_id].course.registrar_code_display = '';

            controller = $controller('PeopleController', {$scope: scope});

            expect(scope.courseInstance['title']).toEqual(ci.title);
            expect(scope.courseInstance['school']).toEqual
                    (ci.course.school_id.toUpperCase());
            expect(scope.courseInstance['term']).toEqual(ci.term.display_name);
            expect(scope.courseInstance['year']).toEqual(ci.term.academic_year);
            expect(scope.courseInstance['course_instance_id']).toEqual(ci.course_instance_id);
            expect(scope.courseInstance['registrar_code_display']).toEqual(
                    ci.course.registrar_code);
            expect(scope.courseInstance['sites']).toEqual('888');
            expect(scope.courseInstance['xlist_status']).toEqual('N/A');

        });
    });

    describe('dt cell render functions', function() {
        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope});
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.flush(1);
        });

        it('renderName', function() {
            var full = {
                profile: {
                    name_first: 'Joe',
                    name_last: 'Student',
                },
            };
            var result = scope.renderName(undefined, undefined, full, undefined);
            expect(result).toEqual('Student, Joe');
        });

        it('renderId', function() {
            var full = {
                profile: {role_type_cd: 'STUDENT'},
                user_id: 123456,
            }
            var result = scope.renderId(undefined, undefined, full, undefined);
            expect(result).toEqual('<badge ng-cloak role="STUDENT"></badge> 123456');
        });

        it('renderSource for registrar-fed', function() {
            var data = 'fasfeed';
            var result = scope.renderSource(data, undefined, undefined, undefined);
            expect(result).toEqual('Registrar Added');
        });

        it('renderSource for manual', function() {
            var data = '';
            var result = scope.renderSource(data, undefined, undefined, undefined);
            expect(result).toEqual('Manually Added');
        });

        it('renderRemove for registrar-fed', function() {
            var full = {source: 'fasfeed', user_id: '1234567890'};
            var meta = {row: 1};
            var result = scope.renderRemove(undefined, undefined, full, meta);
            var expectedResult = '<div class="text-center">' +
                                 '<i class="fa fa-trash-o fa-trash-disabled">' +
                                 '</i></div>';
            expect(result).toEqual(expectedResult);
        });

        it('renderRemove for manual', function() {
            var full = {source: 'peopletool', user_id: '9876543210'};
            var meta = {row: 2};
            var result = scope.renderRemove(undefined, undefined, full, meta);
            var expectedResult = '<div class="text-center">' +
                                 '<a href="" ng-click="confirmRemove(' +
                                 'dtInstance.DataTable.data()[2])" ' +
                                 'data-sisid="9876543210">' +
                                 '<i class="fa fa-trash-o ">' +
                                 '</i></a></div>';
            expect(result).toEqual(expectedResult);
        });
    });

    describe('controller methods which act purely locally', function() {
        // group these so that we can init the scope/controllers/directives
        // such that we're just testing the controller methods
        beforeEach(function() {
            var ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'methods without side effects tests',
            };
            courseInstances.instances[ci.course_instance_id] = ci;
            controller = $controller('PeopleController', {$scope: scope});
        });

        describe('closeAlert', function() {
            it('should work when an alert is present', function() {
                scope.messages.testAlert = 'This is a test';  // contents don't matter
                scope.closeAlert('testAlert');
                expect(scope.messages.testAlert).toBeNull();
            });
            
            it('should not blow up when no alert is present', function() {
                scope.messages.testAlert = null;
                scope.closeAlert('testAlert');
                expect(scope.messages.testAlert).toBeNull();
            });

        });

        describe('compareRoles', function() {
            it('should sort as expected', function() {
                var roles = [
                    {active: 0, prime_role_indicator: ''},
                    {active: 1, prime_role_indicator: ''},
                    {active: 0, prime_role_indicator: 'N'},
                    {active: 1, prime_role_indicator: 'N'},
                    {active: 0, prime_role_indicator: 'Y'},
                    {active: 1, prime_role_indicator: 'Y'},
                ];
                var afterSorting = [
                    {active: 1, prime_role_indicator: 'Y'},
                    {active: 1, prime_role_indicator: 'N'},
                    {active: 1, prime_role_indicator: ''},
                    {active: 0, prime_role_indicator: 'Y'},
                    {active: 0, prime_role_indicator: 'N'},
                    {active: 0, prime_role_indicator: ''},
                ];

                roles.sort(scope.compareRoles);
                expect(roles).toEqual(afterSorting);
            });
        });

        describe('disableAddUserButton', function() {
            // the state of the add user button depends on the contents of
            // the search field
            it('should disable if a search is in progress', function() {
                scope.operationInProgress = true;
                expect(scope.disableAddToCourseButton()).toBe(true);
            });
            it('should disable if there is no search term', function() {
                scope.searchTerms = '';
                expect(scope.disableAddToCourseButton()).toBe(true);
            });
            it('is enabled if there are search terms and no operation is ' +
                'in progress', function() {
                scope.searchTerms = '12345678, a@b.com';
                expect(scope.disableAddToCourseButton()).toBe(false);
            });
        });

        describe('filterSearchResults', function() {
            // NOTE: relies on compareRoles() working properly.  mocking
            //       its results wasn't worth it.
            it('should not blow up on empty input', function() {
                expect(scope.filterSearchResults([])).toEqual([]);
            });

            it('should return one role per univ_id', function() {
                var searchResults = [
                    {univ_id: 123, active: 0, prime_role_indicator: ''},
                    {univ_id: 123, active: 1, prime_role_indicator: 'Y'},
                    {univ_id: 456, active: 0, prime_role_indicator: 'Y'},
                    {univ_id: 456, active: 1, prime_role_indicator: ''},
                    {univ_id: 789, active: 0, prime_role_indicator: 'Y'},
                ];
                var filtered = scope.filterSearchResults(searchResults);
                var uniq = {};
                filtered.forEach(function(r) { uniq[r.univ_id] = true; });
                var filteredIds = Object.keys(uniq);
                filteredIds.sort();

                // if the filtered results have duplicate ids in them, then
                // either filtered.length will be > 3, or the ids we're
                // expecting won't match what's in filteredIds.
                expect(filtered.length).toEqual(3);
                expect(filteredIds).toEqual(['123', '456', '789']);
            });
        });

        describe('handleAjaxError', function() {
            it('should log an error', function() {
                var expectedMessage = 
                    "Error attempting to GET https://tea.pot: 418 I'm a teapot: {}";
                scope.handleAjaxError({}, 418, {},
                                      {method: 'GET', url: 'https://tea.pot'},
                                      "I'm a teapot");
                expect($log.error.logs).toEqual([[expectedMessage]]);
            });
        });

        describe('isUnivID', function() {
            // all valid IDs, should return true
            [{description: 'numbers', testString: '12345678'},
             {description: 'letters', testString: 'abcdefgh'},
             {description: 'alphanumeric', testString: 'a1b2c3d4'},
            ].forEach(function(test) {
                it('should return true for ' + test.description, function() {
                    expect(scope.isUnivID(test.testString)).toBe(true);
                });
            });

            // not valid IDs, should return false
            [{description: 'has @', testString: '1234@678'},
             {description: 'too short', testString: '1234567'},
             {description: 'too long', testString: 'abcdefghi'},
            ].forEach(function(test) {
                it('should return false for ' + test.description, function() {
                    expect(scope.isUnivID(test.testString)).toBe(false);
                });
            });
        });

        describe('selectRole', function() {
            it('should set the role on the scope', function() {
                var role = {roleId: 123};
                scope.selectRole(role);
                expect(scope.selectedRole).toEqual(role);
            });
        });

        describe('clearMessages', function(){
            it('should set all messages to null', function(){
                var messageBuckets = ['warnings'];
                var messageKeys = ['progress', 'success'];
                var scopeKeys = ['removeFailure'];
                var trackingKeys = ['failures', 'successes', 'total',
                    'totalFailures'];
                var expectNoMessages = function() {
                    messageBuckets.forEach(function (bucket) {
                        expect(scope.messages[bucket]).toEqual([]);
                    });
                    messageKeys.forEach(function (key) {
                        expect(scope.messages[key]).toBeNull();
                    });
                    scopeKeys.forEach(function (key) {
                        expect(scope[key]).toBeNull();
                    });
                    trackingKeys.forEach(function (key) {
                        expect(scope.tracking[key]).toEqual(0);
                    });
                };

                // fresh scope should be clear/clean
                expectNoMessages();

                messageBuckets.forEach(function (bucket) {
                    scope.messages[bucket].push({ type: 'test'});
                });
                messageKeys.forEach(function (key) {
                    scope.messages[key] = 1;  // random, meaningless number
                });
                scopeKeys.forEach(function (key) {
                    scope[key] = 1;  // random, meaningless number
                });
                trackingKeys.forEach(function (key) {
                    scope.tracking[key] = 1;  // random, meaningless number
                });

                // refreshed scope should also be clear/clean
                scope.clearMessages();
                expectNoMessages();
            });
        });
    });

    describe('confirmRemove', function() {
        beforeEach(function() {
            var ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'confirmRemove test',
            };
            courseInstances.instances[ci.course_instance_id] = ci;
            controller = $controller('PeopleController', {$scope: scope});
        });

        it('should stick the instance on the scope', function() {
            scope.confirmRemove();
            expect(scope.confirmRemoveModalInstance).not.toBeNull();
        });

        it('should call removeMembership and remove itself from the scope on close',
           function() {
               var membership = {};
               spyOn(scope, 'removeMembership');
               scope.confirmRemove();
               scope.$digest();  // resolves modal instantiation
               scope.confirmRemoveModalInstance.close(membership);
               scope.$digest();  // resolves confirmRemoveModalInstance result
               expect(scope.removeMembership).toHaveBeenCalled();
               expect(scope.confirmRemoveModalInstance).toBeNull();
           }
        );
    });

    describe('removeMembership', function() {
        var membership = {
            profile: {
                name_first: 'Bob',
                name_last: 'Dobbs',
            },
            role: {
                role_id: 0,
            },
            user_id: 'bobdobbs',
        };
        var courseMembershipURL = coursePeopleURL + membership.user_id;

        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope});
            clearInitialCourseInstanceFetch();
            scope.dtInstance = {reloadData: function(){}};
            spyOn(scope.dtInstance, 'reloadData');
        });

        it('should handle success', function() {
            var expectedSuccess = JSON.parse(JSON.stringify(membership));
            angular.extend(expectedSuccess,
                {alertType: 'success', searchTerm: 'Dobbs, Bob', type: 'remove'}
            );

            scope.removeMembership(membership);

            $httpBackend.expectDELETE(courseMembershipURL).respond(204, '');
            $httpBackend.flush(1);

            expect(scope.messages.success).toEqual(expectedSuccess);
            expect(scope.dtInstance.reloadData).toHaveBeenCalled();
        });

        it('should show the correct alert for a 404 no such user', function() {
            var expectedFailure = JSON.parse(JSON.stringify(membership));
            expectedFailure.type = 'noSuchUser';

            scope.removeMembership(membership);
            $httpBackend.expectDELETE(courseMembershipURL)
                .respond(404, '{"detail": "User not found."}');
            $httpBackend.flush(1);

            expect(scope.removeFailure).toEqual(expectedFailure);
            expect(scope.dtInstance.reloadData).toHaveBeenCalled();
        });

        it('should show the correct alert for a 404 no such course', function() {
            var expectedFailure = JSON.parse(JSON.stringify(membership));
            expectedFailure.type = 'noSuchCourse';

            scope.removeMembership(membership);
            $httpBackend.expectDELETE(courseMembershipURL)
                .respond(404, '{"detail": "Course instance not found."}');
            $httpBackend.flush(1);

            expect(scope.removeFailure).toEqual(expectedFailure);
            expect(scope.dtInstance.reloadData).not.toHaveBeenCalled();
        });


        it('should show the correct alert for an unexpected 404', function() {
            var expectedFailure = JSON.parse(JSON.stringify(membership));
            expectedFailure.type = 'unexpected404';

            scope.removeMembership(membership);
            $httpBackend.expectDELETE(courseMembershipURL)
                .respond(404, '{"detail": "Not even if you paid me"}');
            $httpBackend.flush(1);

            expect(scope.removeFailure).toEqual(expectedFailure);
            expect(scope.dtInstance.reloadData).not.toHaveBeenCalled();
        });

        it('should show the correct alert for a 500 canvas error', function() {
            var expectedFailure = JSON.parse(JSON.stringify(membership));
            expectedFailure.type = 'canvasError';

            scope.removeMembership(membership);
            $httpBackend.expectDELETE(courseMembershipURL)
                .respond(500, '{"detail": "User could not be removed from Canvas."}');
            $httpBackend.flush(1);

            expect(scope.removeFailure).toEqual(expectedFailure);
            expect(scope.dtInstance.reloadData).toHaveBeenCalled();
        });

        it('should show the correct alert for a 500 non-canvas error', function() {
            var expectedFailure = JSON.parse(JSON.stringify(membership));
            expectedFailure.type = 'serverError';

            scope.removeMembership(membership);
            $httpBackend.expectDELETE(courseMembershipURL)
                .respond(500, '{"detail": "Nope."}');
            $httpBackend.flush(1);

            expect(scope.removeFailure).toEqual(expectedFailure);
            expect(scope.dtInstance.reloadData).not.toHaveBeenCalled();
        });

        it('should show the fallback alert for a non-404/500 error', function() {
            var expectedFailure = JSON.parse(JSON.stringify(membership));
            expectedFailure.type = 'unknown';

            scope.removeMembership(membership);
            $httpBackend.expectDELETE(courseMembershipURL)
                .respond(418, "I'm a teapot!");
            $httpBackend.flush(1);

            expect(scope.removeFailure).toEqual(expectedFailure);
            expect(scope.dtInstance.reloadData).not.toHaveBeenCalled();
        });
    });
});
