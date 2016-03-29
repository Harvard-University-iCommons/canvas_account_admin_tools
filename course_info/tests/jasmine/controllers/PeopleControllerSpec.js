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
        $httpBackend, $window, $log, $uibModal, $templateCache;
    var controller, scope;
    var courseInstanceId = 1234567890;
    var courseInstanceURL =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fcourse_instances%2F' + courseInstanceId + '%2F';
    var coursePeopleURL = courseInstanceURL + 'people%2F';

    // set up the test environment
    beforeEach(function() {
        // load in the app and the templates-as-module
        module('CourseInfo');
        module('templates');
        inject(function(_$controller_, _$rootScope_, _$routeParams_, _courseInstances_,
                        _$compile_, _djangoUrl_, _$httpBackend_, _$window_, _$log_,
                        _$uibModal_, _$templateCache_) {
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

        it('should set all message vars to null', function(){
            ['success', 'addWarning',
                'addPartialFailure', 'removeFailure'].forEach(function(scopeAttr) {
                var thing = scope[scopeAttr];
                expect(thing).toBeNull();
            });
        });

        it('should have a bunch of non-null variables set up', function() {
            ['dtColumns', 'dtOptions', 'roles', 'searchInProgress',
                'searchResults', 'searchTerm', 'selectedResult',
                'selectedRole'].forEach(function(scopeAttr) {
                var thing = scope[scopeAttr];
                expect(thing).not.toBeUndefined();
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

        describe('clearSearchResults', function() {
            it('should empty any search results', function() {
                scope.searchResults = [{}];  // contents don't matter
                scope.clearSearchResults();
                expect(scope.searchResults).toEqual([]);
            });
        });

        describe('closeAlert', function() {
            it('should work when an alert is present', function() {
                scope.testAlerts = 'This is a test';  // contents don't matter
                scope.closeAlert('testAlerts');
                expect(scope.testAlerts).toBeNull();
            });
            
            it('should not blow up when no alert is present', function() {
                scope.testAlerts = null;
                scope.closeAlert('testAlerts');
                expect(scope.testAlerts).toBeNull();
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
                scope.addPartialFailure = 'There has been a failure';
                scope.addWarning = 'There has been an error';
                scope.success = 'User added';
                scope.removeFailure = 'Error removing user';

                scope.clearMessages();
                ['success', 'addWarning',
                    'partialFailureData', 'removeFailure'].forEach(function(scopeAttr) {
                    var thing = scope[scopeAttr];
                    expect(thing).toBeNull();
                });
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
            expectedSuccess.action = 'added to';

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
            expect(scope.success).toEqual(expectedSuccess);
            expect(scope.dtInstance.reloadData.calls.count()).toEqual(1);
        });

        it('should alert and reload the datatable on a canvas partial failure',
           function() {
               var partialFailureResponse = {
                   detail: "Error while enrolling user USER in Canvas section sis_section_id:SECTION. Canvas API error details: 403: {u'message': u\"Can't add an enrollment to a concluded course.\"}",
               };
               var expectedSuccess =
                   JSON.parse(JSON.stringify(enrollmentDetails.results[0]));

               var partialFailureData = {
                   searchTerm: searchTerm,
                   text: partialFailureResponse.detail,
               };
               expectedSuccess.searchTerm = searchTerm;
               expectedSuccess.action = 'added to';
               expectedSuccess.partialFailureData = partialFailureData;

               // mock out the datatable so we can verify that it gets reloaded
               scope.dtInstance = {reloadData: function(){}};
               spyOn(scope.dtInstance, 'reloadData');

               // call it
               scope.addUserToCourse(searchTerm, user);

               // trigger the ajax calls
               $httpBackend.expectPOST(coursePeopleURL, user)
                           .respond(500, JSON.stringify(partialFailureResponse));
               $httpBackend.expectGET(enrollmentDetailsURL)
                           .respond(200, JSON.stringify(enrollmentDetails));
               $httpBackend.flush(2);

               // check to see if it's reacting correctly
               expect(scope.success).toEqual(expectedSuccess);
               expect(scope.dtInstance.reloadData.calls.count()).toEqual(1);
           }
        );

        it('should warn on failure to add the user', function() {
            spyOn(scope, 'handleAjaxError');

            scope.addUserToCourse(searchTerm, user);

            $httpBackend.expectPOST(coursePeopleURL, user).respond(500, '');
            $httpBackend.flush(1);

            expect(scope.handleAjaxError.calls.count()).toEqual(1);
            expect(scope.addWarning).toEqual({type: 'addFailed',
                                             searchTerm: searchTerm});
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

               expect(scope.addPartialFailure).toEqual(expectedPartialFailure);
               expect(scope.handleAjaxError.calls.count()).toEqual(1);
           }
        );
    });

    describe('handleLookupResults', function() {
        // NOTE: relies on filterSearchResults() working properly.  mocking
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
               expect(scope.addWarning).toEqual(expectedWarning);
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
               expect(scope.addWarning).toEqual(expectedWarning);
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
               var filteredResults = scope.filterSearchResults(
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
            var ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'confirmRemove test',
            };
            courseInstances.instances[ci.course_instance_id] = ci;
            controller = $controller('PeopleController', {$scope: scope});
            scope.dtInstance = {reloadData: function(){}};
            spyOn(scope.dtInstance, 'reloadData');
        });

        it('should handle success', function() {
            var expectedSuccess = JSON.parse(JSON.stringify(membership));
            expectedSuccess.action = 'removed from';
            expectedSuccess.searchTerm = 'Dobbs, Bob';

            scope.removeMembership(membership);

            $httpBackend.expectDELETE(courseMembershipURL).respond(204, '');
            $httpBackend.flush(1);

            expect(scope.success).toEqual(expectedSuccess);
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
