describe('Unit testing DetailsController', function() {
    var $controller, $rootScope, $routeParams, courseInstances, $compile, djangoUrl,
        $httpBackend, $window, $log, $uibModal, $sce;

    var controller, scope;
    var courseInstanceId = 1234567890;
    var courseInstanceURL =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fcourse_instances%2F' + courseInstanceId + '%2F';

    // set up the test environment
    beforeEach(function () {
        module('CourseInfo');
        inject(function (_$controller_, _$rootScope_, _$routeParams_, _courseInstances_,
                         _$compile_, _djangoUrl_, _$httpBackend_, _$window_, _$log_,
                         _$uibModal_, _$sce_) {
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
            $sce = _$sce_;

            // this comes from django_auth_lti, just stub it out so that the $httpBackend
            // sanity checks in afterEach() don't fail
            $window.globals = {
                append_resource_link_id: function (url) {
                    return url;
                }
            };
        });
        scope = $rootScope.$new();
        $routeParams.courseInstanceId = courseInstanceId;
    });

    afterEach(function () {
        // sanity checks to make sure no http calls are still pending
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

        // DI sanity check
    it('should inject the providers we requested', function() {
        [$controller, $rootScope, $routeParams, courseInstances, $compile,
         djangoUrl, $httpBackend, $window, $log, $sce].forEach(function(thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    describe('setup', function() {
        beforeEach(function() {
            controller = $controller('DetailsController', {$scope: scope });
        });

        afterEach(function() {
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.flush(1);
        });

        it('should set the course instance id', function() {
            expect(dc.courseInstanceId).toEqual($routeParams.courseInstanceId);
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
                }
            };
        });

        it('should work when CourseInstance is empty', function() {
            controller = $controller('DetailsController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.flush(1);
            expect(dc.courseInstance['title']).toEqual(ci.title);
            expect(dc.courseInstance['school']).toEqual(ci.course.school_id.toUpperCase());
        });

        it('should work when CourseInstance returns invalid id', function() {
            controller = $controller('DetailsController', {$scope: scope});
            ci.course_instance_id = 12345;
            spyOn($log, 'error');
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.flush(1);
            expect($log.error).toHaveBeenCalled();
        });
    });

    describe('stripQuotes', function(){
        var ci;
        beforeEach(function() {
            // if we want to pull the instance id from $routeParams, this has
            // to be in a beforeEach(), can't be in a describe().
            ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: '"Test Title"',
                course: {
                    school_id: 'abc',
                    registrar_code_display: '2222'
                }
            };
        });

        it('should strip the quotes from the string', function(){
            controller = $controller('DetailsController', {$scope: scope});
            result = dc.stripQuotes(ci.title);
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.flush(1);
            expect('Test Title').toEqual(result);
        });
    });

});