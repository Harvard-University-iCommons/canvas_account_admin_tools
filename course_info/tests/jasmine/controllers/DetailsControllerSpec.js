describe('Unit testing DetailsController', function () {
    var $controller, $rootScope, $routeParams, courseInstances, $compile, djangoUrl,
        $httpBackend, $window, $log, $uibModal, $sce, $templateCache;

    var controller, scope;
    var courseInstanceId = 1234567890;
    var courseInstanceURL =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fcourse_instances%2F' + courseInstanceId + '%2F';

    var peopleURL =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fcourse_instances%2F' + courseInstanceId +
        '%2Fpeople%2F&-source=xreg_map';

    var deleteSiteUrl =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fcourse_instances%2F' + courseInstanceId + '%2Fsites%2F999%2F';

    var postSiteUrl =
        '/angular/reverse/?djng_url_name=icommons_rest_api_proxy&djng_url_args' +
        '=api%2Fcourse%2Fv2%2Fcourse_instances%2F' + courseInstanceId + '%2Fsites%2F';

    // set up the test environment
    beforeEach(function () {
        // load the app and the templates-as-module
        module('CourseInfo');
        module('templates');
        inject(function (_$controller_, _$rootScope_, _$routeParams_, _courseInstances_,
                         _$compile_, _djangoUrl_, _$httpBackend_, _$window_, _$log_,
                         _$uibModal_, _$sce_, _$templateCache_) {
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
            $templateCache = _$templateCache_;

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
            djangoUrl, $httpBackend, $window, $log, $sce, $templateCache].forEach(function (thing) {
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
                    registrar_code: 'ILE-2222',
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
                    registrar_code: 'ILE-2222',
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
                sync_to_canvas: '1',
                exclude_from_isites: '0',
                exclude_from_catalog: '0'
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
                ci.course.registrar_code_display);
            expect(dc.courseInstance['sites']).toEqual(ci.sites);
            expect(dc.courseInstance['xlist_status']).toEqual('N/A');
            expect(dc.courseInstance['description']).toEqual('<p>hello</p>');
            // members.count is not defined it should equal 0
            expect(dc.courseInstance['members']).toEqual(100);
            expect(dc.courseInstance['sync_to_canvas']).toEqual(ci.sync_to_canvas);
            expect(dc.courseInstance['exclude_from_isites']).toEqual(ci.exclude_from_isites);
            expect(dc.courseInstance['exclude_from_catalog']).toEqual(ci.exclude_from_catalog);

        });

    });
        
    describe('fetchCourseInstanceDetails', function() {

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
                    registrar_code: 'ILE-2222',
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

        it('should handle both successful responses even if they arrive ' +
            'separately', function(){
            courseInstances.instances[ci.course_instance_id] = ci;
            dc = $controller('DetailsController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify(members));
            $httpBackend.flush(2);
            expect(dc.courseInstance['title']).toEqual(ci.title);
            expect( dc.courseInstance['members']).toEqual(members.count);
        });

        it('should still handle the course instance data even if the ' +
            'member data fetch fails', function(){
            courseInstances.instances[ci.course_instance_id] = ci;
            dc = $controller('DetailsController', {$scope: scope});
            spyOn(dc, 'handleCourseInstanceResponse');
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify(ci));
            $httpBackend.expectGET(peopleURL).respond(500);
            $httpBackend.flush(2);
            expect(dc.courseInstance['title']).toEqual(ci.title);
        });
    });

    describe('submitCourseDetailsForm', function() {
        var ci;
        var members;
        var expectedPatchData = {
                "description":"this is a test",
                "instructors_display":"test teacher",
                "location":"test room",
                "meeting_time":"test oclock",
                "notes":"test notes",
                "short_title":"test short title",
                "sub_title":"test sub title",
                "title":"test title",
                "sync_to_canvas": 1,
                "exclude_from_isites":0,
                "exclude_from_catalog":0,
                "conclude_date":null
            };

        beforeEach(function () {
            ci = {
                course_instance_id: $routeParams.courseInstanceId,
                title: 'Test Course Title',
                short_title: 'Test',
                sub_title: 'Jasime is your friend',
                description: '<p>hello</p>',
                sync_to_canvas : 1,
                exclude_from_isites:0,
                exclude_from_catalog:0,
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
                    registrar_code: 'ILE-2222',
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

        it('should call backend with only the editable form fields', function(){
            courseInstances.instances[ci.course_instance_id] = ci;
            dc = $controller('DetailsController', {$scope: scope});
            spyOn(dc, 'showNewGlobalAlert');
            dc.formDisplayData = {
                'description': 'this is a test',
                'instructors_display': 'test teacher',
                'location': 'test room',
                'meeting_time': 'test oclock',
                'notes': 'test notes',
                'short_title': 'test short title',
                'sub_title': 'test sub title',
                'title': 'test title',
                'sync_to_canvas' : 1,
                'exclude_from_isites':0,
                'exclude_from_catalog':0,
                "conclude_date":null
            };

            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.flush(2);
            dc.submitCourseDetailsForm();
            $httpBackend.expectPATCH(courseInstanceURL, expectedPatchData).respond(201, JSON.stringify({status: "success"}));
            $httpBackend.flush(1);
            expect(dc.showNewGlobalAlert).toHaveBeenCalledWith('updateSucceeded');
        });

        it('should show a message if successful and update the local ' +
            'course instance data', function(){
            courseInstances.instances[ci.course_instance_id] = ci;
            dc = $controller('DetailsController', {$scope: scope});
            spyOn(dc, 'showNewGlobalAlert');
            dc.formDisplayData = {
                'description': 'this is a test',
                'instructors_display': 'test teacher',
                'location': 'test room',
                'meeting_time': 'test oclock',
                'notes': 'test notes',
                'short_title': 'test short title',
                'sub_title': 'test sub title',
                'title': 'test title',
                'sync_to_canvas' : 1,
                'exclude_from_isites':0,
                'exclude_from_catalog':0,
                "conclude_date":null
            };

            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.flush(2);
            dc.submitCourseDetailsForm();
            $httpBackend.expectPATCH(courseInstanceURL, expectedPatchData).respond(201, JSON.stringify({status: "success"}));
            $httpBackend.flush(1);
            expect(dc.showNewGlobalAlert).toHaveBeenCalledWith('updateSucceeded');
            expect(dc.courseInstance['title']).toBe('test title');
        });

        it('should show a message if unsuccessful and not update the ' +
            'local course instance data', function(){
            courseInstances.instances[ci.course_instance_id] = ci;
            dc = $controller('DetailsController', {$scope: scope});
            spyOn(dc, 'showNewGlobalAlert');
            dc.formDisplayData = {
                'description': 'this is a test',
                'instructors_display': 'test teacher',
                'location': 'test room',
                'meeting_time': 'test oclock',
                'notes': 'test notes',
                'short_title': 'test short title',
                'sub_title': 'test sub title',
                'title': 'test title',
                'sync_to_canvas' : 1,
                'exclude_from_isites':0,
                'exclude_from_catalog':0,
                "conclude_date":null
            };

            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.flush(2);
            dc.submitCourseDetailsForm();
            $httpBackend.expectPATCH(courseInstanceURL, expectedPatchData).respond(500);
            $httpBackend.flush(1);
            expect(dc.showNewGlobalAlert).toHaveBeenCalledWith('updateFailed', '');
            expect(dc.courseInstance['title']).not.toBe('test title');
        });
    });

    describe('editableInputDirective', function() {
        var compile, scope, directiveElem;
        beforeEach(function () {
             inject(function($compile, $rootScope){
                compile = $compile;
                scope = $rootScope.$new();
              });
              directiveElem = getCompiledElement();
        });

        function getCompiledElement(){
            var element = angular.element('<hu-editable-input ' +
                    'editable="dc.editable"' +
                    'is-loading="dc.isUndefined(dc.courseInstance.term)"' +
                    'form-value="dc.courseInstance.term"' +
                    'model-value="testModelValue"' +
                    'maxlength="500"' +
                    'field="test-name"' +
                'label="test label">' +
                '</hu-editable-input>');
            var compiledElement = compile(element)(scope);
            scope.$digest();
            return compiledElement;
        }

        it('should substitute the right stuff for id, name, and label', function(){
            dc = $controller('DetailsController', {$scope: scope});
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.flush(2);
            expect(directiveElem.find('label').text().trim()).toBe('test label');
            expect(directiveElem.find('input').prop('id')).toBe('input-course-test-name');
            expect(directiveElem.find('input').prop('name')).toBe('input-course-test-name');
            expect(directiveElem.find('input').prop('maxlength')).toBe(500);
        });

        // skipping this test as I'm pretty sure it's not
        // doing the right thing, I left the code so when we
        // revisit we can see what we tried to do. This will be
        // included in the tech debt item TLT-2539
        it('should show an input element if called with editable=true ' +
            'and the value should be equal to the form\'s copy of the ' +
            'model data');

        // ditto comment above
        it('should show regular non-editable text if called with ' +
            'editable=false or no editable attribute and show the model ' +
            'value, not the form copy of the model value');

        // skipping the following test, they are tech debt in TLT-2539
        it('should only show the label and the loading indicator ' +
            'while loading, and hide the loading indicator when no ' +
            'longer loading');
    });

    describe('getCourseDescription', function() {
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
        it('should display the course title if title is present', function () {
            var course = { title: 'ABC'};
            result = dc.getCourseDescription(course);
            expect(result).toEqual('ABC');
        });

        it('should dipslay the course short title if title is not present and short title is', function() {
            var course = { title: '', short_title: 'short'};
            result = dc.getCourseDescription(course);
            expect(result).toEqual('short');
        });

        it('should display Untitled Course when no title or short title are present', function(){
            var course = { title: '', short_title: ''};
            result = dc.getCourseDescription(course);
            expect(result).toEqual('Untitled Course');
        });

        it('should display Untitled Course when no data is present', function(){
            var course = {};
            result = dc.getCourseDescription(course);
            expect(result).toEqual('Untitled Course');
        });

        it('should display title if both title and short title are present', function(){
            var course = { title: 'ABC', short_title: 'short'};
            result = dc.getCourseDescription(course);
            expect(result).toEqual('ABC');
        });
    });
});
