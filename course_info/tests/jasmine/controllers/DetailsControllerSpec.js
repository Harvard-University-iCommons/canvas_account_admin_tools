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

    describe('controller setup/initialization', function () {
        beforeEach(function () {
            dc = $controller('DetailsController', {$scope: scope});
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
        it('should populate the form immediately if course instance data is ' +
            'available from the routeParams/previous screen, and then ' +
            'continue to fetch course instance details to fill in missing ' +
            'data');
    });

    describe('handleCourseInstanceResponse', function () {
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
                },
                term: {
                    display_name: 'Summer 2015',
                    academic_year: '2015',
                }
            };
            members = {
                count: 100
            };
        });

        it('should fill in details from the course instance detail endpoint ' +
            'when no course instance is provided by the ' +
            'routeParams/previous screen', function () {
            var dc = $controller('DetailsController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify(members));
            $httpBackend.flush(2);
            expect(dc.courseInstance['title']).toEqual(ci.title);
            expect(dc.courseInstance['school']).toEqual(ci.course.school_id.toUpperCase());
            expect(dc.courseInstance['members']).toEqual(100);
        });

        it('should override details from the course instance info provided ' +
            'by the routeParams/previous screen with refreshed/updated data ' +
            'from the course instance detail endpoint ');
        it('should log an error when CourseInstance returns an invalid id', function () {
            controller = $controller('DetailsController', {$scope: scope});
            ci.course_instance_id = 12345;
            spyOn($log, 'error');
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify(members));
            $httpBackend.flush(2);
            expect($log.error).toHaveBeenCalled();
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
                description: '<p>hello</p>',
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
                    departments: [
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

        it('should format the course instance data for the UI ', function () {
            courseInstances.instances[ci.course_instance_id] = ci;
            dc = $controller('DetailsController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify(members));
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
            expect(dc.courseInstance['course_instance_id']).toEqual(ci.course_instance_id);
            expect(dc.courseInstance['registrar_code_display']).toEqual(
                ci.course.registrar_code_display + ' (' + ci.course.course_id + ')');
            expect(dc.courseInstance['sites']).toEqual(ci.sites);
            expect(dc.courseInstance['xlist_status']).toEqual('N/A');
            expect(dc.courseInstance['description']).toEqual('<p>hello</p>');
            // members.count is not defined it should equal 0
            expect(dc.courseInstance['members']).toEqual(100);

        });

    });
        
    describe('fetchCourseInstanceDetails', function() {
        it('should handle both successful responses even if they arrive ' +
            'separately');
        it('should still handle the course instance data even if the ' +
            'member data fetch fails');
    });

    describe('submitCourseDetailsForm', function() {
        it('should call backend with only the editable form fields');
        it('should show a message if successful and update the local ' +
            'course instance data');
        it('should show a message if unsuccessful and not update the ' +
            'local course instance data');
    });

    describe('editableInputDirective', function() {
        it('should substitute the right stuff for id, name, and label');
        it('should show an input element if called with editable=true ' +
            'and the value should be equal to the form\'s copy of the ' +
            'model data');
        it('should show regular non-editable text if called with ' +
            'editable=false or no editable attribute and show the model ' +
            'value, not the form copy of the model value');
        it('should show only show the label and the loading indicator ' +
            'while loading, and hide the loading indicator when no ' +
            'longer loading');
    });

    describe('fieldLabelWrapperDirective', function() {
        it('should call backend with only the editable form fields');
        it('should show a message if successful and update the local ' +
            'course instance data');
        it('should show a message if unsuccessful and not update the ' +
            'local course instance data');
    });

    describe('end-to-end tests - form interaction', function() {
        it('should reset all data when form is reset and show reset ' +
            'message');
        it('should call backend on submit');
        it('should show editable fields and form interaction buttons for ' +
            'an editable course instance');
        it('should show non-editable fields for a typical course ' +
            'instance and no form interaction buttons');
    });

});