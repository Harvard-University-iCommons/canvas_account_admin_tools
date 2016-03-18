describe('Unit testing DetailsController', function () {
    var $controller, $rootScope, $routeParams, courseInstances, $compile, djangoUrl,
        $httpBackend, $window, $log, $uibModal, $sce;

    var controller, scope;
    var courseInstanceId = 1234567890;
    var courseInstanceURL =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fcourse_instances%2F' + courseInstanceId + '%2F';

    var peopleURL =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fcourse_instances%2F' + courseInstanceId + '%2Fpeople%2F';

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
    it('should inject the providers we requested', function () {
        [$controller, $rootScope, $routeParams, courseInstances, $compile,
            djangoUrl, $httpBackend, $window, $log, $sce].forEach(function (thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    describe('setup', function () {
        beforeEach(function () {
            controller = $controller('DetailsController', {$scope: scope});
        });

        afterEach(function () {
            // handle the course instance get from setTitle, so we can always
            // assert at the end of a test that there's no pending http calls.
            $httpBackend.expectGET(courseInstanceURL).respond(200, '');
            $httpBackend.expectGET(peopleURL).respond(200, '');
            $httpBackend.flush(2);
        });

        it('should set the course instance id', function () {
            expect(dc.courseInstanceId).toEqual($routeParams.courseInstanceId);
        });

    });

    describe('setCourseInstance', function () {
        var ci;
        var members;
        beforeEach(function () {
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
            members = {
                count: 100
            };
        });

        it('should work when CourseInstance is empty', function () {
            var dc = $controller('DetailsController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify(members));
            $httpBackend.flush(2);
            expect(dc.courseInstance['title']).toEqual(ci.title);
            expect(dc.courseInstance['school']).toEqual(ci.course.school_id.toUpperCase());
            expect(dc.courseInstance['members']).toEqual(100);
        });

        it('should work when CourseInstance returns invalid id', function () {
            controller = $controller('DetailsController', {$scope: scope});
            ci.course_instance_id = 12345;
            spyOn($log, 'error');
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify(members));
            $httpBackend.flush(2);
            expect($log.error).toHaveBeenCalled();
        });
    });

    describe('stripQuotes', function () {
        var ci;
        var members;
        beforeEach(function () {
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
            members = {
                count: 100
            };
        });

        it('should strip the quotes from the string', function () {
            controller = $controller('DetailsController', {$scope: scope});
            result = dc.stripQuotes(ci.title);
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify(members));
            $httpBackend.flush(2);
            expect('Test Title').toEqual(result);
        });
    });

    describe('getFormattedCourseInstance', function () {
        var ci;
        var members;
        beforeEach(function () {
            ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'Test Title',
                short_title: 'Test',
                sub_title: 'Jasime is your friend',
                description: '"<p>hello</p>"',
                sites: [
                    {
                        external_id: 'https://x.y.z/888',
                        site_id: '888',
                        map_type: 'official'
                    },
                     {
                        external_id: 'https://x.y.z/999',
                        site_id: '999',
                        map_type: 'unofficial'
                    }
                ],
                course: {
                    school_id: 'abc',
                    registrar_code_display: '2222',
                    course_id: '789',
                    course_groups: [
                        {
                            name: 'group one',
                            id: 1
                        },
                        {
                            name: 'group two',
                            id: 2
                        }
                    ],
                    departments : [
                        {
                            name: 'dept1',
                            id: 1
                        }
                    ]
                },
                term: {
                    display_name: 'Summer 2015',
                    academic_year: '2015',
                },
                primary_xlist_instances: [],
            };

            members = {
                count: 100
            };
        });

        it('format the course instance data for the UI ', function () {
            courseInstances.instances[ci.course_instance_id] = ci;
            dc = $controller('DetailsController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify({}));
            $httpBackend.flush(2);
            expect(dc.courseInstance['title']).toEqual(ci.title);
            expect(dc.courseInstance['short_title']).toEqual(ci.short_title);
            expect(dc.courseInstance['sub_title']).toEqual(ci.sub_title);
            expect(dc.courseInstance['school']).toEqual
            (ci.course.school_id.toUpperCase());
            expect(dc.courseInstance['term']).toEqual(ci.term.display_name);
            expect(dc.courseInstance['course_groups']).toEqual(ci.course.course_groups);
            expect(dc.courseInstance['departments']).toEqual(ci.course.departments);
            expect(dc.courseInstance['year']).toEqual(ci.term.academic_year);
            expect(dc.courseInstance['cid']).toEqual(ci.course_instance_id);
            expect(dc.courseInstance['registrar_code_display']).toEqual(
                ci.course.registrar_code_display + ' (' + ci.course.course_id + ')');
            expect(dc.courseInstance['sites']).toEqual(ci.sites);
            expect(dc.courseInstance['xlist_status']).toEqual('N/A');
            expect(dc.courseInstance['description']).toEqual('<p>hello</p>');
            // members.count is not defined it should equal 0
            expect(dc.courseInstance['members']).toEqual(0);

        });

        it('should deal with an empty ci', function () {
            dc = $controller('DetailsController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify({}));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify({}));
            $httpBackend.flush(2);
            expect(dc.courseInstance).toEqual(undefined);
        });
    });
});