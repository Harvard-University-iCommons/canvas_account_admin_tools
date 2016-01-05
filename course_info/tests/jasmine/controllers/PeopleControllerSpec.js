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
        $httpBackend, $window, $log;
    var controller, scope;
    var courseInstanceId = 1234567890;
    var courseInstanceURL =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fcourse_instances%2F' + courseInstanceId + '%2F';
    var coursePeopleURL = courseInstanceURL + 'people%2F';

    // set up the test environment
    beforeEach(function() {
        module('CourseInfo');
        inject(function(_$controller_, _$rootScope_, _$routeParams_, _courseInstances_,
                        _$compile_, _djangoUrl_, _$httpBackend_, _$window_, _$log_) {
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            $routeParams = _$routeParams_;
            courseInstances = _courseInstances_;
            $compile = _$compile_;
            djangoUrl = _djangoUrl_;
            $httpBackend = _$httpBackend_;
            $window = _$window_;
            $log = _$log_;

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
         djangoUrl, $httpBackend, $window, $log].forEach(function(thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
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
            ['dtColumns', 'dtOptions', 'partialFailures', 'roles',
             'searchInProgress', 'searchResults', 'searchTerm', 'selectedResult',
             'selectedRole', 'successes', 'warnings'].forEach(function(scopeAttr) {
                var thing = scope[scopeAttr];
                expect(thing).not.toBeUndefined();
                expect(thing).not.toBeNull();
            });
        });
    });

    describe('setTitle', function() {
        var ci;
        beforeEach(function() {
            // if we want to pull the instance id from $routeParams, this has
            // to be in a beforeEach(), can't be in a describe().
            ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'Test Title',
            };
        });

        it('should work when courseInstances has the course instance', function() {
            courseInstances.instances[ci.course_instance_id] = ci;
            controller = $controller('PeopleController', {$scope: scope});
            expect(scope.title).toEqual(ci.title);
        });

        it('should work whenCourseInstances is empty', function() {
            controller = $controller('PeopleController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL)
                        .respond(200, JSON.stringify(ci));
            $httpBackend.flush(1);
            expect(scope.title).toEqual(ci.title);
        });
    });

    describe('dt cell render functions', function() {
        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope});
        });

        afterEach(function() {
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

        describe('clearSearchResults', function() {
            it('should empty any search results', function() {
                scope.searchResults = [{}];  // contents don't matter
                scope.clearSearchResults();
                expect(scope.searchResults).toEqual([]);
            });
        });

        describe('closeAlert', function() {
            it('should work when an alert is present', function() {
                scope.testAlerts = [{}];  // contents don't matter
                scope.closeAlert('testAlerts', 0);
                expect(scope.testAlerts).toEqual([]);
            });
            
            it('should not blow up when no alert is present', function() {
                scope.testAlerts = [];
                scope.closeAlert('testAlerts', 0);
                expect(scope.testAlerts).toEqual([]);
            });

            it('should only remove the index requested', function() {
                scope.testAlerts = [1, 2, 3];
                scope.closeAlert('testAlerts', 1);
                expect(scope.testAlerts).toEqual([1,3]);
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
            // the search field, on whether a lookup has returned multiple
            // results, and on whether any of those results have been selected
            it('should disable if a search is in progress', function() {
                scope.searchInProgress = true;
                expect(scope.disableAddUserButton()).toBe(true);
            });
            it('should enable if the search had multiple results and one is selected',
               function() {
                   scope.searchResults = [{}, {}]; // contents don't matter, only length
                   scope.selectedResult = {id: 123};
                   expect(scope.disableAddUserButton()).toBe(false);
               }
            );
            it('should disable if the search had multiple results and none are selected',
               function() {
                   scope.searchResults = [{}]; // contents don't matter, only length
                   scope.selectedResult = {id: null};
                   expect(scope.disableAddUserButton()).toBe(true);
               }
            );
            it('should enable if a search term has been entered and there are no results',
               function() {
                   scope.searchTerm = 'bob';
                   expect(scope.disableAddUserButton()).toBe(false);
               }
            );
            it('should disable if there is no search term or results', function() {
                expect(scope.disableAddUserButton()).toBe(true);
            });
        });

        describe('filterResults', function() {
            // NOTE: relies on compareRoles() working properly.  mocking
            //       its results wasn't worth it.
            it('should not blow up on empty input', function() {
                expect(scope.filterResults([])).toEqual([]);
            });

            it('should return one role per univ_id', function() {
                var searchResults = [
                    {univ_id: 123, active: 0, prime_role_indicator: ''},
                    {univ_id: 123, active: 1, prime_role_indicator: 'Y'},
                    {univ_id: 456, active: 0, prime_role_indicator: 'Y'},
                    {univ_id: 456, active: 1, prime_role_indicator: ''},
                    {univ_id: 789, active: 0, prime_role_indicator: 'Y'},
                ];
                var filtered = scope.filterResults(searchResults);
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
                    "Error getting data from https://tea.pot: 418 I'm a teapot: {}";
                scope.handleAjaxError({}, 418, {}, {url: 'https://tea.pot'},
                                      "I'm a teapot");
                expect($log.error.logs).toEqual([[expectedMessage]]);
            });
        });

        describe('isEmailAddress', function() {
            // TODO - steal test addresses from real email parsing library?
            // all valid addresses, should return true
            [{description: 'simple email address', testString: 'bob_dobbs@harvard.edu'},
             {description: 'email address with long domain',
              testString: 'bob_dobbs@very.specific.server.harvard.edu'},
            ].forEach(function(test) {
                it('should return true for ' + test.description, function() {
                    expect(scope.isEmailAddress(test.testString)).toBe(true);
                });
            });

            // not addresses, should return false
            [{description: 'series of digits', testString: '123456789'},
             {description: '@ but no .', testString: 'bob_dobbs@harvard'},
             {description: '. but no @', testString: 'bob_dobbs.harvard.edu'},
            ].forEach(function(test) {
                it('should return false for ' + test.description, function() {
                    expect(scope.isEmailAddress(test.testString)).toBe(false);
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
    });

    describe('addUser', function() {
        beforeEach(function() {
            var ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'addUser tests',
            };
            courseInstances.instances[ci.course_instance_id] = ci;
            controller = $controller('PeopleController', {$scope: scope});
            spyOn(scope, 'addUserToCourse');
            spyOn(scope, 'lookup');
        });

        it('should call lookup if there are no search results', function() {
            scope.searchResults = [];
            scope.addUser('bob');
            expect(scope.addUserToCourse.calls.count()).toEqual(0);
            expect(scope.lookup.calls.count()).toEqual(1);
            expect(scope.lookup.calls.argsFor(0)).toEqual(['bob']);
        });

        it('should log an error if called with a single search result', function() {
            scope.searchResults = [{}]; // contents don't matter
            scope.addUser('bob');
            expect($log.error.logs).toEqual(
                [['Add user button pressed while we have a single search result']]);
            expect(scope.addUserToCourse.calls.count()).toEqual(0);
            expect(scope.lookup.calls.count()).toEqual(0);
        });

        it('should call lookup if there are multiple search results and none selected',
           function() {
               scope.searchResults = [{}, {}];
               scope.addUser('bob');
               expect(scope.addUserToCourse.calls.count()).toEqual(0);
               expect(scope.lookup.calls.count()).toEqual(1);
               expect(scope.lookup.calls.argsFor(0)).toEqual(['bob']);
           }
        );

        it('should call addUserToCourse if there are multiple results and one selected',
           function() {
               scope.searchResults = [{}, {}];
               scope.selectedResult = {id: 999};
               scope.selectedRole = {roleId: 888};
               scope.addUser('bob');
               expect(scope.addUserToCourse.calls.count()).toEqual(1);
               expect(scope.addUserToCourse.calls.argsFor(0)).toEqual(
                       ['bob', {user_id: scope.selectedResult.id,
                                role_id: scope.selectedRole.roleId}]);
           }
        );
    });

    describe('addUserToCourse', function() {
        var user = {user_id: 'bobdobbs', role_id: 0};
        var searchTerm = 'bob_dobbs@harvard.edu';
        var enrollmentDetailsURL = coursePeopleURL + '&user_id=' + user.user_id;
        var enrollmentDetails = {
            results: [{
                profile: {
                    name_last: 'Dobbs',
                    name_first: 'Bob',
                    role_type_cd: 'STUDENT',
                    univ_id: 'bobdobbs',
                },
                role: {
                    role_name: 'Student',
                }
            }],
        };

        beforeEach(function() {
            var ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'addUserToCourse test',
            };
            courseInstances.instances[ci.course_instance_id] = ci;
            controller = $controller('PeopleController', {$scope: scope});
            scope.searchInProgress = true;
            scope.searchResults = [{}];
        });

        afterEach(function() {
            // no matter what, we should end the search and clear the results.
            expect(scope.searchInProgress).toBe(false);
            expect(scope.searchResults).toEqual([]);
        });

        it('should alert and reload the datatable on success', function() {
            var expectedSuccess = 
                JSON.parse(JSON.stringify(enrollmentDetails.results[0]));
            expectedSuccess.searchTerm = searchTerm;

            // mock out the datatable so we can verify that it gets reloaded
            scope.dtInstance = {reloadData: function(){}};
            spyOn(scope.dtInstance, 'reloadData');

            // call it
            scope.addUserToCourse(searchTerm, user);

            // trigger the ajax calls
            $httpBackend.expectPOST(coursePeopleURL, user)
                        .respond(201, JSON.stringify(user)); 
            $httpBackend.expectGET(enrollmentDetailsURL)
                        .respond(200, JSON.stringify(enrollmentDetails));
            $httpBackend.flush(2);

            // check to see if it's reacting correctly
            expect(scope.successes).toEqual([expectedSuccess]);
            expect(scope.dtInstance.reloadData.calls.count()).toEqual(1);
        });

        it('should alert on a partial failure', function() {
            var partialFailureResponse = 
                JSON.parse(JSON.stringify(enrollmentDetails.results[0]));
            partialFailureResponse.detail = 'Some kind of partial failure';
            var expectedSuccess = 
                JSON.parse(JSON.stringify(enrollmentDetails.results[0]));
            expectedSuccess.searchTerm = searchTerm;
            var expectedPartialFailure = {
                searchTerm: searchTerm,
                text: partialFailureResponse.detail,
            };

            // mock out the datatable so we can verify that it gets reloaded
            scope.dtInstance = {reloadData: function(){}};
            spyOn(scope.dtInstance, 'reloadData');

            // call it
            scope.addUserToCourse(searchTerm, user);

            // trigger the ajax calls
            $httpBackend.expectPOST(coursePeopleURL, user)
                        .respond(201, JSON.stringify(partialFailureResponse)); 
            $httpBackend.expectGET(enrollmentDetailsURL)
                        .respond(200, JSON.stringify(enrollmentDetails));
            $httpBackend.flush(2);

            // check to see if it's reacting correctly
            expect(scope.successes).toEqual([expectedSuccess]);
            expect(scope.partialFailures).toEqual([expectedPartialFailure]);
            expect(scope.dtInstance.reloadData.calls.count()).toEqual(1);
        });

        it('should warn on failure to add the user', function() {
            spyOn(scope, 'handleAjaxError');

            scope.addUserToCourse(searchTerm, user);

            $httpBackend.expectPOST(coursePeopleURL, user).respond(500, '');
            $httpBackend.flush(1);

            expect(scope.handleAjaxError.calls.count()).toEqual(1);
            expect(scope.warnings).toEqual([{type: 'addFailed',
                                             searchTerm: searchTerm}]);
        });

        it('should handle a failure to get user enrollment after an apparent add success',
           function() {
               var expectedPartialFailure = {
                   searchTerm: searchTerm,
                   text: 'Add to course seemed to succeed, but we received ' +
                         'an error trying to retrieve the user\'s course details.',
               };
               spyOn(scope, 'handleAjaxError');

               scope.addUserToCourse(searchTerm, user);

               $httpBackend.expectPOST(coursePeopleURL, user)
                           .respond(201, JSON.stringify(user)); 
               $httpBackend.expectGET(enrollmentDetailsURL).respond(404, '');
               $httpBackend.flush(2);

               expect(scope.partialFailures).toEqual([expectedPartialFailure]);
               expect(scope.handleAjaxError.calls.count()).toEqual(1);
           }
        );
    });

    describe('handleLookupResults', function() {
        // NOTE: relies on filterResults() working properly.  mocking
        //       its results wasn't worth it.
        beforeEach(function() {
            var ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'handleLookupResults test',
            };
            courseInstances.instances[ci.course_instance_id] = ci;
            controller = $controller('PeopleController', {$scope: scope});
            scope.searchInProgress = true;
        });

        it('should warn and disable progress if the user is already enrolled',
           function() {
               var peopleResult = {}; // content doesn't matter
               var memberResult = {
                   data: {results:
                              [{profile: {name_last: 'Dobbs',
                                          name_first: 'Bob'}}]},
                   config: {searchTerm: 'bob_dobbs@harvard.edu'},
               };
               var expectedWarning = {
                   type: 'alreadyInCourse',
                   fullName: 'Dobbs, Bob',
                   memberships: memberResult.data.results,
                   searchTerm: 'bob_dobbs@harvard.edu',
               };

               scope.handleLookupResults([peopleResult, memberResult]);
               expect(scope.warnings).toEqual([expectedWarning]);
               expect(scope.searchInProgress).toBe(false);
           }
        );

        it('should warn and disable progress if the user is not found',
           function() {
               var peopleResult = {
                   data: {results: []},
                   config: {searchTerm: 'bob_dobbs@harvard.edu'},
               };
               var memberResult = {data: {results: []}};
               var expectedWarning = {
                   type: 'notFound',
                   searchTerm: 'bob_dobbs@harvard.edu',
               };

               scope.searchTerm = 'bob_dobbs@harvard.edu';
               scope.handleLookupResults([peopleResult, memberResult]);
               expect(scope.warnings).toEqual([expectedWarning]);
               expect(scope.searchInProgress).toBe(false);
           }
        );

        it('should call addUserToCourse if one result is found', function() {
            var peopleResult = {
                data: {
                    results: [
                        {univ_id: 456, active: 0, prime_role_indicator: 'Y'},
                    ],
                },
                config: {searchTerm: 'bob_dobbs@harvard.edu'},
            };
            var memberResult = {data: {results: []}};
            spyOn(scope, 'addUserToCourse');

            scope.selectedRole = {roleId: 123};
            scope.handleLookupResults([peopleResult, memberResult]);
            expect(scope.addUserToCourse.calls.count()).toEqual(1);
            expect(scope.addUserToCourse.calls.argsFor(0)).toEqual(
                       ['bob_dobbs@harvard.edu',
                        {user_id: 456, role_id: 123}]);
            expect(scope.searchInProgress).toBe(true);
        })

        it('should show choices and disable progress for multiple results',
           function() {
               var peopleResult = {
                   data: {
                       results: [
                           {univ_id: 456, active: 0, prime_role_indicator: 'Y'},
                           {univ_id: 789, active: 0, prime_role_indicator: 'Y'},
                       ],
                   },
                   config: {searchTerm: 'bob_dobbs@harvard.edu'},
               };
               var memberResult = {data: {results: []}};
               var filteredResults = scope.filterResults(
                                         peopleResult.data.results);

               scope.handleLookupResults([peopleResult, memberResult]);
               expect(scope.searchResults).toEqual(filteredResults);
               expect(scope.searchInProgress).toBe(false);
           }
        );
    });

    describe('lookup', function() {
        beforeEach(function() {
            var ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'lookup test',
            };
            courseInstances.instances[ci.course_instance_id] = ci;
            controller = $controller('PeopleController', {$scope: scope});
            spyOn(scope, 'handleLookupResults');
        });

        it('queries by email when appropriate', function() {
            var searchTerm = 'bob_dobbs@harvard.edu';
            var peopleURLValidate = function(uri) {
                return validateURIHasParameters(
                           uri, {'email_address': searchTerm});
            };
            var memberURLValidate = function(uri) {
                return validateURIHasParameters(
                           uri, {'profile.email_address': searchTerm});
            };

            scope.lookup(searchTerm);
            $httpBackend.expectGET(peopleURLValidate).respond(200, '');
            $httpBackend.expectGET(memberURLValidate).respond(200, '');
            $httpBackend.flush(2);
        });

        it('queries by user id when appropriate', function() {
            var searchTerm = 'bobdobbs';
            var peopleURLValidate = function(uri) {
                return validateURIHasParameters(
                           uri, {'univ_id': searchTerm});
            };
            var memberURLValidate = function(uri) {
                return validateURIHasParameters(
                           uri, {'user_id': searchTerm});
            };

            scope.lookup(searchTerm);
            $httpBackend.expectGET(peopleURLValidate).respond(200, '');
            $httpBackend.expectGET(memberURLValidate).respond(200, '');
            $httpBackend.flush(2);
        });

        it('logs errors from the people endpoint', function() {
            var searchTerm = 'bob_dobbs@harvard.edu';
            var peopleURLValidate = function(uri) {
                return validateURIHasParameters(
                           uri, {'email_address': searchTerm});
            };
            var memberURLValidate = function(uri) {
                return validateURIHasParameters(
                           uri, {'profile.email_address': searchTerm});
            };
            spyOn(scope, 'handleAjaxError');
            scope.lookup('bob_dobbs@harvard.edu');
            $httpBackend.expectGET(peopleURLValidate).respond(500, '');
            $httpBackend.expectGET(memberURLValidate).respond(200, '');
            $httpBackend.flush(2);
            expect(scope.handleAjaxError.calls.count()).toEqual(1);
        });

        it('logs errors from the course people endpoint', function() {
            var searchTerm = 'bob_dobbs@harvard.edu';
            var peopleURLValidate = function(uri) {
                return validateURIHasParameters(
                           uri, {'email_address': searchTerm});
            };
            var memberURLValidate = function(uri) {
                return validateURIHasParameters(
                           uri, {'profile.email_address': searchTerm});
            };
            spyOn(scope, 'handleAjaxError');
            scope.lookup('bob_dobbs@harvard.edu');
            $httpBackend.expectGET(peopleURLValidate).respond(200, '');
            $httpBackend.expectGET(memberURLValidate).respond(500, '');
            $httpBackend.flush(2);
            expect(scope.handleAjaxError.calls.count()).toEqual(1);
        });
    });
});
