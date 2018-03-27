describe('Unit testing CreateNewCourseController', function() {
    var $controller, $rootScope, $httpBackend, $uibModal, $log, djangoUrl,
        $qGlobal, $window;

    var scope;
    var scopeDefaults = {
        'course': {
            code: '',
            codeString: '',
            codeType: '',
            shortTitle: '',
            term: null,
            title: ''
        },
        'departments': {},
        'school': {id: 'gse', name: 'Harvard GSE'},
        'terms': []
    };

    var apiBaseURL = '/angular/reverse/?djng_url_name=' +
        'icommons_rest_api_proxy&djng_url_args=api%2Fcourse%2Fv2%2F';
    var api = {
        'data': {
            'course_instances_filtered_by_course_and_term': { results: [
                {section: '001'},
                {section: '002'},
                {section: 'abc'}
            ]},
            'courses': { results: [
                {id: '1'}
            ]},
            'course_sites_post': {
                course_site_id: 1
            },
            'departments': { results: [
                {short_name: 'SB', department_id: '1'},
                {short_name: 'ILE', department_id: '2'},
                {short_name: 'other', department_id: '3'}
            ]},
            'site_maps_post': {
                site_map_id: 1
            },
            'terms': { results: [
                {term_id: '1', display_name:'recent'},
                {term_id: '2', display_name:'older'}
            ]}
        },
        'urls': {
            'course_sites': apiBaseURL + 'course_sites%2F',
            'departments': apiBaseURL + 'departments%2F&school='
                           + scopeDefaults.school.id + '&limit=1000',
            'site_maps': apiBaseURL + 'site_maps%2F',
            'terms': apiBaseURL + 'terms%2F&school=' + scopeDefaults.school.id +
                     '&active=True&limit=1000' +
                     '&with_end_date=True&with_start_date=True' +
                     '&ordering=-end_date,term_code__sort_order',
            'create_course': '/angular/reverse/?djng_url_name=canvas_site_creator%3Aapi_create_canvas_course',
            'create_course_instance': apiBaseURL+'course_instances%2F',
            'copy_template': '/angular/reverse/?djng_url_name=canvas_site_creator%3Aapi_copy_from_canvas_template'
        }
    };

    // set up the test environment
    beforeEach(function() {
        module('app');
        inject(function(_$controller_, _$rootScope_, _$httpBackend_,
                        _$uibModal_, _$log_, _djangoUrl_, $q, _$window_) {
            $controller = _$controller_;
            djangoUrl = _djangoUrl_;
            $httpBackend = _$httpBackend_;
            $log = _$log_;
            $rootScope = _$rootScope_;
            $uibModal = _$uibModal_;
            $qGlobal = $q;
            $window = _$window_;

            // this comes from django_auth_lti, just stub it out so that the
            // $httpBackend sanity checks in afterEach() don't fail
            $window.globals = {
                append_resource_link_id: function(url) { return url; }
            };
        });
        scope = $rootScope.$new();

        var controller = $controller('CreateNewCourseController', {
            $scope: scope, school: scopeDefaults.school});

        // handle the loadTermsAndDepartments() requests on controller init
        $httpBackend.expectGET(api.urls.terms)
            .respond(200, JSON.stringify(api.data.terms));
        $httpBackend.expectGET(api.urls.departments)
            .respond(200, JSON.stringify(api.data.departments));
        $httpBackend.flush(2); // flush the loadTermsAndDepartments() requests
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    afterEach(function() {
        // sanity checks to make sure no http calls are still pending
        $httpBackend.verifyNoOutstandingExpectation();
        $httpBackend.verifyNoOutstandingRequest();
    });

    // DI sanity check
    it('should inject the providers we requested', function() {
        [$controller, $rootScope, $httpBackend, $uibModal, $log, djangoUrl,
            $window].forEach(function(thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    describe('getExistingCourse', function() {
        var apiURL;
        var mockGetExistingCourseInstancePromise = function() {
            var deferred = $qGlobal.defer();
            deferred.resolve();  // resolve immediately for testing
            return deferred.promise;
        };

        beforeEach(function() {
            scope.course.code = 'ILE-test';

            apiURL = apiBaseURL + 'courses%2F'
                + '&limit=1000'
                + '&registrar_code=' + scope.course.code
                + '&school=' + scope.school.id;

            spyOn(scope, 'getExistingCourseInstances')
                .and.callFake(mockGetExistingCourseInstancePromise);
            spyOn(scope, 'handleAjaxErrorWithMessage');
        });

        it('should not fetch course instances if no course exists',
            function () {
            var noResults = {results:[]};
            scope.getExistingCourse();

            $httpBackend.expectGET(apiURL)
                .respond(200, JSON.stringify(noResults));
            $httpBackend.flush(1);

            expect(scope.getExistingCourseInstances).not.toHaveBeenCalled();
            expect(scope.handleAjaxErrorWithMessage).not.toHaveBeenCalled();
            expect(scope.existingCourse).toBeNull();
        });

        it('should fetch course instances if course exists', function () {
            var singleResult = api.data.courses;
            scope.getExistingCourse();

            $httpBackend.expectGET(apiURL)
                .respond(200, JSON.stringify(singleResult));
            $httpBackend.flush(1);
            scope.$digest();  // resolves getExistingCourseInstance mock

            expect(scope.getExistingCourseInstances).toHaveBeenCalled();
            expect(scope.handleAjaxErrorWithMessage).not.toHaveBeenCalled();
            expect(scope.existingCourse).toEqual(api.data.courses.results[0]);
        });

        it('should log a warning if multiple courses exist but continue ' +
            'to fetch course instances using the first course in the list',
            function() {
            var multipleResults = angular.copy(api.data.courses);
            multipleResults.results.push({'id': 2});
            scope.getExistingCourse();

            $httpBackend.expectGET(apiURL)
                .respond(200, JSON.stringify(multipleResults));
            $httpBackend.flush(1);
            scope.$digest();  // resolves getExistingCourseInstance mock

            expect(scope.getExistingCourseInstances).toHaveBeenCalled();
            expect(scope.handleAjaxErrorWithMessage).not.toHaveBeenCalled();
            expect(scope.existingCourse).toEqual(api.data.courses.results[0]);
        });

        it('should fail gracefully', function() {
            scope.getExistingCourse();

            $httpBackend.expectGET(apiURL).respond(500);  // mock server error
            $httpBackend.flush(1);

            expect(scope.getExistingCourseInstances).not.toHaveBeenCalled();
            expect(scope.handleAjaxErrorWithMessage).toHaveBeenCalled();
            expect(scope.existingCourse).toBeNull();
        });
    });

    describe('getExistingCourseInstances', function() {
        var apiURL;

        beforeEach(function() {
            scope.course.term = '1';
            scope.existingCourse = {course_id: '1'};

            apiURL = apiBaseURL + 'course_instances%2F'
                + '&course__course_id=' + scope.existingCourse.course_id
                + '&limit=1000'
                + '&term=' + scope.course.term;

            spyOn(scope, 'handleAjaxErrorWithMessage');
        });

        it('should get a course instance list and all sections for those CIs',
            function () {

            var apiTestData = api.data.course_instances_filtered_by_course_and_term;
            var expectedExistingSections = apiTestData.results.map(function(ci){
                return ci.section;
            });

            scope.getExistingCourseInstances();
            $httpBackend.expectGET(apiURL)
                .respond(200, JSON.stringify(apiTestData));
            $httpBackend.flush(1);

            expect(scope.existingSections).toEqual(expectedExistingSections);
            expect(scope.handleAjaxErrorWithMessage).not.toHaveBeenCalled();
        });

        it('should not mark any sections if no course instances match that ' +
            'course and term', function () {

            var apiTestData = { results: []};

            scope.getExistingCourseInstances();
            $httpBackend.expectGET(apiURL)
                .respond(200, JSON.stringify(apiTestData));
            $httpBackend.flush(1);

            expect(scope.existingSections).toEqual([]);
            expect(scope.handleAjaxErrorWithMessage).not.toHaveBeenCalled();
        });

        it('should fail gracefully', function () {
            scope.getExistingCourseInstances();
            $httpBackend.expectGET(apiURL).respond(500);  // mock server error
            $httpBackend.flush(1);

            expect(scope.existingSections).toEqual([]);
            expect(scope.handleAjaxErrorWithMessage).toHaveBeenCalled();
        });
    });

    describe('getNextSectionId', function() {
        it('should get next available number', function () {
            var sectionList = ["001", "002"];
            var nextId = scope.getNextSectionId(sectionList);
            expect(nextId).toEqual("003");
        });
        it('should handle empty lists', function() {
            var nextId = scope.getNextSectionId([]);
            expect(nextId).toEqual("001");
        });
        it('should handle lists with non-numeric values', function () {
            var sectionList = ["not", "a number"];
            var nextId = scope.getNextSectionId(sectionList);
            expect(nextId).toEqual("001");
        });
    });

    describe('handleAjaxErrorWithMessage', function() {
        it('should log and show a failure modal', function () {
            var expectedMessage =
                "Error attempting to GET https://tea.pot: 418 I'm a teapot: {}";
            var badResponse = {
                config: {method: 'GET', url: 'https://tea.pot'},
                data: {},
                status: 418,
                statusText: "I'm a teapot"
            };
            spyOn(scope, 'cancelCreateNewCourseInstance').and.callThrough();

            scope.handleAjaxErrorWithMessage(badResponse);
            $httpBackend.expectGET(
                'partials/create_new_course_failure_modal.html')
                .respond(200, '');
            $httpBackend.flush(1);
            scope.failureModal.close();  // simulate user input
            scope.$digest();  // resolves failureModal result

            expect($log.error.logs).toEqual([[expectedMessage]]);
            expect(scope.cancelCreateNewCourseInstance).toHaveBeenCalled();
            expect(scope.failureModal).toBeNull();
            expect(scope.courseCreationInProgress).toBe(false);
        });
    });

    describe('setCourseCode', function() {
        it('should allow valid registrar codes', function() {
            scope.course = {
                codeString: 'abc-123_456..XYZ',
                codeType: 'test'
            };
            scope.setCourseCode();
            expect(scope.errorInCourseCode).toBeNull();
            expect(scope.course.code).toBe('test-abc-123_456..XYZ');
        });
        it('should show error for invalid registrar codes', function() {
            invalidCodes = ['a v', '', '^&*(', 'é'];
            for (var i=0, len=invalidCodes.length; i < len; i++) {
                scope.course = {
                    codeString: invalidCodes[i],
                    codeType: 'test'
                };
                scope.setCourseCode();
                expect(scope.errorInCourseCode).not.toBeNull();
                expect(scope.course.code).toBe('');
            }
        });
    });

    describe('createCanvasCourse', function(){
        var  mockCopyFromTemplate = function() {
            var deferred = $qGlobal.defer();
            deferred.resolve();  // resolve immediately for testing
            return deferred.promise;
        };
        beforeEach(function(){
            scope.newCourseInstance = {
                term: {meta_term_id:'1900-99'},
                course_instance_id: 123456,
                section: 1234
            };
            scope.departments = {
                'test': 'colgsas'
            };
            scope.course = {
                codeType: 'TEST',
                code: 'TEST-123',
                title: 'this is a test',
                shortTitle: 'test course'
            };
            scope.school = {
                id: 'colgsas'
            };
            spyOn(scope, 'copyFromTemplate').and.callFake(mockCopyFromTemplate);

        });
        it('should make the call to the rest api to create a new course', function(){
            var expectedPostData = {
                dept_id: 'dept:colgsas',
                course_instance_id: 123456,
                course_code: 'TEST-123',
                section_id: 1234,
                term_id: '1900-99',
                title: 'this is a test',
                short_title: 'test course',
                school: 'colgsas'
            };
            spyOn(scope, 'updateTablesWithCanvasCourseInfo');
            spyOn(scope, 'handleAjaxErrorWithMessage');

            scope.createCanvasCourse();

            $httpBackend.expectPOST(api.urls.create_course, expectedPostData)
                .respond(201, {status: "success"});
            $httpBackend.flush(1);
            expect(scope.canvasCourse.status).toBe("success");
            expect(scope.updateTablesWithCanvasCourseInfo).toHaveBeenCalled();
            expect(scope.handleAjaxErrorWithMessage)
                .not.toHaveBeenCalled();
        });
        it('should not invoke template copy if a template is not selected '
            , function () {
            scope.selectedTemplate = 'None';
            spyOn(scope, 'updateTablesWithCanvasCourseInfo');
            scope.createCanvasCourse();
            $httpBackend.expectPOST(api.urls.create_course)
                .respond(201, {status: "success"});
            $httpBackend.flush(1);
            expect(scope.copyFromTemplate)
                .not.toHaveBeenCalled();
        });
        it('should invoke template copy if a template is selected '
            , function () {
            scope.selectedTemplate = '123';
            spyOn(scope, 'updateTablesWithCanvasCourseInfo');
            spyOn(scope, 'handleAjaxErrorWithMessage');
            scope.createCanvasCourse();
            $httpBackend.expectPOST(api.urls.create_course)
                .respond(201, {status: "success"});
            $httpBackend.flush(1);
            expect(scope.copyFromTemplate)
                .toHaveBeenCalled();
        });
        it('should handle errors gracefully', function(){
            spyOn(scope, 'updateTablesWithCanvasCourseInfo');
            spyOn(scope, 'handleAjaxErrorWithMessage');

            scope.createCanvasCourse();

            $httpBackend.expectPOST(api.urls.create_course).respond(500);
            $httpBackend.flush(1);
            expect(scope.updateTablesWithCanvasCourseInfo).not.toHaveBeenCalled();
            expect(scope.handleAjaxErrorWithMessage).toHaveBeenCalled();
        });
    });

    describe('updateTablesWithCanvasCourseInfo', function(){
        it('should make the call to the rest api to update data', function() {
            scope.newCourseInstance = {
                term: {
                    academic_year: 2016,
                    term_code: 'Spring'
                },
                course_instance_id: 123456,
                section_id: 1234
            };
            scope.canvasCourse = {
                id: 12345
            };
            scope.sync_to_canvas = 1;

            spyOn(scope, 'postCourseSiteAndMap');
            spyOn(scope, 'handleAjaxErrorWithMessage');
            scope.updateTablesWithCanvasCourseInfo();
            data = {
                canvas_course_id: scope.canvasCourse.id,
                sync_to_canvas: 1
            };
            $httpBackend.expectPATCH(api.urls.patch, data)
                .respond(201, JSON.stringify({status: "success"}));
            $httpBackend.flush(1);
            expect(scope.postCourseSiteAndMap).toHaveBeenCalled();
            expect(scope.handleAjaxErrorWithMessage)
                .not.toHaveBeenCalled();
        });
        it('should handle errors gracefully', function(){

            scope.newCourseInstance = {
                term: {
                    academic_year: 2016,
                    term_code: 'Spring'
                },
                course_instance_id: 123456,
                section_id: 1234
            };
            scope.canvasCourse = {
                id: 12345
            };
            scope.sync_to_canvas = 1;

            spyOn(scope, 'postCourseSiteAndMap');
            spyOn(scope, 'handleAjaxErrorWithMessage');
            scope.updateTablesWithCanvasCourseInfo();
            $httpBackend.expectPATCH(api.urls.patch, data).respond(500);
            $httpBackend.flush(1);
            expect(scope.postCourseSiteAndMap).not.toHaveBeenCalled();
            expect(scope.handleAjaxErrorWithMessage).toHaveBeenCalled();
        });
    });

    describe('postCourseSiteAndMap', function(){
        it('should create a site map with the right course information and ' +
            'set site_map_id on scope when finished', function () {

            scope.canvasCourse = {
                id: 12345
            };
            window.globals.CANVAS_URL = 'someurl';
            var testUrl = 'someurl/courses/'+scope.canvasCourse.id;
            scope.newCourseInstance = {
                canvas_course_url: testUrl
            };
            var expectedPostData = {
                external_id: testUrl,
                site_type_id : 'external'
            };
            spyOn(scope, 'handleAjaxErrorWithMessage');
            spyOn(scope, 'postSiteMap');

            scope.postCourseSiteAndMap();

            $httpBackend.expectPOST(api.urls.course_sites, expectedPostData)
                .respond(201, JSON.stringify(api.data.course_sites_post));
            $httpBackend.flush(1);

            expect(scope.newCourseInstance.course_site_id)
                .toBe(api.data.course_sites_post.course_site_id);
            expect(scope.postSiteMap).toHaveBeenCalled();
            expect(scope.handleAjaxErrorWithMessage)
                .not.toHaveBeenCalled();
        });

        it('should handle errors gracefully', function () {
            scope.canvasCourse = {
                id: 12345
            };
            window.globals.CANVAS_URL = 'someurl';
            var testUrl = 'someurl/courses/'+scope.canvasCourse.id;
            scope.newCourseInstance = {
                canvas_course_url: testUrl
            };

            spyOn(scope, 'handleAjaxErrorWithMessage');
            spyOn(scope, 'postSiteMap');

            scope.postCourseSiteAndMap();
            var expectedPostData = {
                external_id: testUrl,
                site_type_id : 'external'
            };
            $httpBackend.expectPOST(api.urls.course_sites, expectedPostData)
                .respond(500);  // simulate server error
            $httpBackend.flush(1);

            expect(scope.newCourseInstance.course_site_id).toBeUndefined();
            expect(scope.postSiteMap).not.toHaveBeenCalled();
            expect(scope.handleAjaxErrorWithMessage).toHaveBeenCalled();
        });
    });

    describe('postSiteMap', function(){
        it('should create a site map with the right course information and ' +
            'set site_map_id on scope when finished', function () {
            scope.newCourseInstance = {
                course_instance_id: 123456,
                course_site_id: 1234
            };
            var expectedPostData = {
                course_instance : scope.newCourseInstance.course_instance_id,
                course_site : scope.newCourseInstance.course_site_id,
                map_type : 'official'
            };
            spyOn(scope, 'handleAjaxErrorWithMessage');
            scope.postSiteMap();

            $httpBackend.expectPOST(api.urls.site_maps, expectedPostData)
                .respond(201, JSON.stringify(api.data.site_maps_post));
            $httpBackend.flush(1);
            expect(scope.courseCreationSuccessful).toBe(true);
            expect(scope.courseCreationInProgress).toBe(false);
            expect(scope.handleAjaxErrorWithMessage)
                .not.toHaveBeenCalled();
        });

        it('should handle errors gracefully', function () {
            scope.newCourseInstance = {};
            spyOn(scope, 'handleAjaxErrorWithMessage');

            scope.postSiteMap();

            $httpBackend.expectPOST(api.urls.site_maps)
                .respond(500);  // simulate server error
            $httpBackend.flush(1);

            expect(scope.newCourseInstance.site_map_id).toBeUndefined();
            expect(scope.handleAjaxErrorWithMessage).toHaveBeenCalled();
        });
    });

    describe('copyFromTemplate', function(){
        it('should copy from the template if a template is selected from ' +
            'the dropdown', function () {
            var expectedPostData = {
                template_id: 1,
                canvas_course_id: 12345
            };
            scope.canvasCourse = {
                id: 12345
            };
            scope.selectedTemplate = 1;
            scope.copyFromTemplate();
            $httpBackend.expectPOST(api.urls.copy_template, expectedPostData)
                .respond(200);
            $httpBackend.flush(1);

        });

        it('should handle errors gracefully', function () {
            scope.canvasCourse = {};
            scope.selectedTemplate = 1;
            spyOn(scope, 'handleAjaxErrorWithMessage');
            scope.copyFromTemplate();
            $httpBackend.expectPOST(api.urls.copy_template)
                .respond(500);  // simulate server error
            $httpBackend.flush(1);
            expect(scope.templateResult).toBeUndefined();
            expect(scope.handleAjaxErrorWithMessage).toHaveBeenCalled();
        });
    });

    describe('handleCreate', function() {
        var mockGetExistingCourseResolvesWithNoCourse = function() {
            var deferred = $qGlobal.defer();
            deferred.resolve();
            return deferred.promise;
        };
        var mockGetExistingCourseResolvesWithCourseAndCourseInstanceFound = function() {
            var deferred = $qGlobal.defer();
            scope.existingCourse = api.data.courses.results[0];
            scope.existingSections = ['001'];
            deferred.resolve();
            return deferred.promise;
        };
        var mockGetExistingCourseResolvesWithCourseButNoCourseInstanceFound = function() {
            var deferred = $qGlobal.defer();
            scope.existingCourse = api.data.courses.results[0];
            deferred.resolve();
            return deferred.promise;
        };
        beforeEach(function() {
            // simulate initial controller state / reset any changes from tests
            scope.existingCourse = null;
            scope.existingSections = [];
        });
        it('should create a course right away if none exists', function () {
            spyOn(scope, 'createCourseAndInstance');
            spyOn(scope, 'prepCourseSectionAndCreateCourse');
            spyOn(scope, 'getExistingCourse')
                .and.callFake(mockGetExistingCourseResolvesWithNoCourse);
            scope.handleCreate();
            scope.$digest();  // resolves getExistingCourse mock
            expect(scope.createCourseAndInstance).toHaveBeenCalled();
            expect(scope.prepCourseSectionAndCreateCourse)
                .not.toHaveBeenCalled();
            expect(scope.existingCourseModal).toBeNull();
        });
        it('should create a course instance right away if a course exists ' +
            'but no course instance exists in that term', function () {
            spyOn(scope, 'createCourseAndInstance');
            spyOn(scope, 'prepCourseSectionAndCreateCourse');
            spyOn(scope, 'getExistingCourse')
                .and.callFake(mockGetExistingCourseResolvesWithCourseButNoCourseInstanceFound);
            scope.handleCreate();
            scope.$digest();  // resolves getExistingCourse mock
            expect(scope.createCourseAndInstance).not.toHaveBeenCalled();
            expect(scope.prepCourseSectionAndCreateCourse).toHaveBeenCalled();
            expect(scope.existingCourseModal).toBeNull();
        });
        it('should prompt for confirmation if a course instance exists for ' +
            'the course in that term, and proceed with creating new course ' +
            'instance/section if user confirms', function () {
            spyOn(scope, 'createCourseAndInstance');
            spyOn(scope, 'prepCourseSectionAndCreateCourse');
            spyOn(scope, 'getExistingCourse')
                .and.callFake(mockGetExistingCourseResolvesWithCourseAndCourseInstanceFound);
            scope.handleCreate();

            $httpBackend.expectGET(
                'partials/create_new_course_existing_course_modal.html')
                .respond(200, '');
            $httpBackend.flush(1);
            scope.$digest();  // resolves getExistingCourse mock

            scope.existingCourseModal.close();  // simulate user input
            scope.$digest();  // resolves modal

            expect(scope.createCourseAndInstance).not.toHaveBeenCalled();
            expect(scope.prepCourseSectionAndCreateCourse).toHaveBeenCalled();
            expect(scope.existingCourseModal).toBeNull();
        });
    });

    describe('loadTermsAndDepartments', function() {
        it('should load up the scope with term list, most recent term, and ' +
            'SB/ILE department list', function () {
            // reset scope variables affected by loadTermsAndDepartments()
            // triggered by controller initialization in top-level beforeEach()
            scope.course = scopeDefaults['course'];
            scope.departments = scopeDefaults['departments'];
            scope.terms = scopeDefaults['terms'];

            scope.loadTermsAndDepartments();
            $httpBackend.expectGET(api.urls.terms)
                .respond(200, JSON.stringify(api.data.terms));
            $httpBackend.expectGET(api.urls.departments)
                .respond(200, JSON.stringify(api.data.departments));
            $httpBackend.flush(2);

            expect(scope.terms).toEqual([
                {id: '1', name: 'recent'},
                {id: '2', name: 'older'}
            ]);
            expect(scope.course.term).toBe('1');
            expect(scope.departments).toEqual({
                'sb': '1',
                'ile': '2'
            });

        });
    });

});
