describe('Unit testing PeopleController', function() {
    var $controller, $rootScope, $routeParams, courseInstances, $compile, djangoUrl,
        $httpBackend, $window;
    var controller, scope;

    // set up the test environment
    beforeEach(function() {
        module('CourseInfo');
        inject(function(_$controller_, _$rootScope_, _$routeParams_, _courseInstances_,
                        _$compile_, _djangoUrl_, _$httpBackend_, _$window_) {
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            $routeParams = _$routeParams_;
            courseInstances = _courseInstances_;
            $compile = _$compile_;
            djangoUrl = _djangoUrl_;
            $httpBackend = _$httpBackend_;
            $window = _$window_;

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
         djangoUrl, $httpBackend, $window].forEach(function(thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    describe('$scope setup', function() {
        afterEach(function() {
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET('/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args=api%2Fcourse%2Fv2%2Fcourse_instances%2F1234567890%2F')
                .respond(200, '');
            $httpBackend.flush(1);
        });

        beforeEach(function() {
            controller = $controller('PeopleController', {$scope: scope });
        });

        it('should set the course instance id', function() {
            expect(scope.courseInstanceId).toEqual($routeParams.courseInstanceId);
        });

        it('should set dtColumns up', function() {
            expect(scope.dtColumns).not.toBeUndefined();
            expect(scope.dtColumns).not.toBeNull();
        });

        it('should set dtOptions up', function() {
            expect(scope.dtOptions).not.toBeUndefined();
            expect(scope.dtOptions).not.toBeNull();
        });

        it('should have a null dtInstance', function() {
            expect(scope.dtInstance).toBeNull();
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
            expect(result).toBe('Student, Joe');
        });

        it('renderId', function() {
            var full = {
                profile: {role_type_cd: 'STUDENT'},
                user_id: 123456,
            }
            var result = scope.renderId(undefined, undefined, full, undefined);
            expect(result).toBe('<badge ng-cloak role="STUDENT"></badge> 123456');
        });

        it('renderSource for registrar-fed', function() {
            var data = 'fasfeed';
            var result = scope.renderSource(data, undefined, undefined, undefined);
            expect(result).toBe('Registrar Added');
        });

        it('renderSource for manual', function() {
            var data = '';
            var result = scope.renderSource(data, undefined, undefined, undefined);
            expect(result).toBe('Manually Added');
        });
    });
});
