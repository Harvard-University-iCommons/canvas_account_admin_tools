describe('Unit testing PeopleController', function() {
    var $controller, $rootScope, $routeParams, courseInstances, $compile, djangoUrl,
        $httpBackend, $window, $log;
    var controller, scope;

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
        $routeParams.courseInstanceId = 1234567890;
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
            $httpBackend.expectGET('/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args=api%2Fcourse%2Fv2%2Fcourse_instances%2F1234567890%2F')
                .respond(200, '');
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
            $httpBackend.expectGET('/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args=api%2Fcourse%2Fv2%2Fcourse_instances%2F1234567890%2F')
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
            $httpBackend.expectGET('/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args=api%2Fcourse%2Fv2%2Fcourse_instances%2F1234567890%2F')
                .respond(200, '');
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
                title: 'Fnord fnord fnord',
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
            it('should sort as expected', function() {
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
                   scope.searchResults = [{}]; // contents don't matter, only length
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
            //       out compareRoles() was not worth it.
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
                expect(filtered.length).toEqual(3);
                expect(filteredIds).toEqual(['123', '456', '789']);
            });
        });
        describe('handleAjaxError', function() {
            it('should log an error', function() {
                var expectedMessage = "Error getting data from https://tea.pot: 418 I'm a teapot: {}";
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
                title: 'Fnord fnord fnord',
            };
            courseInstances.instances[ci.course_instance_id] = ci;
            controller = $controller('PeopleController', {$scope: scope});
            spyOn(scope, 'addUserToCourse');
            spyOn(scope, 'lookup');
        });
        it('should log an error if called with a single search result', function() {
            scope.searchResults = [{}]; // contents don't matter
            scope.addUser('bob');
            expect($log.error.logs).toEqual(
                [['Add user button pressed while we have a single search result']]);
            expect(scope.addUserToCourse.calls.count()).toEqual(0);
            expect(scope.lookup.calls.count()).toEqual(0);
        });
    });
    describe('addUserToCourse', function() {});
    describe('handleLookupResults', function() {});
    describe('lookup', function() {});
});
