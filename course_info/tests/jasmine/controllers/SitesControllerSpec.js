describe('Unit testing SitesController', function () {
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
            dc = $controller('SitesController', {$scope: scope});
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

    describe('associateNewSiteHandleKey', function(){
        it('should call associateNewSite when a user hits the enter key', function(){
            spyOn(dc, 'validNewSiteURL').and.returnValue(true);
            spyOn(dc, 'associateNewSite');
            var aEvent = angular.element.Event('keydown');
            aEvent.keyCode = 13;
            $("input").trigger(aEvent);
            dc.associateNewSiteHandleKey(aEvent);
            expect(dc.validNewSiteURL).toHaveBeenCalled();
            expect(dc.associateNewSite).toHaveBeenCalled();

        });

        xit('should not call associateNewSite when a user enteres an invalid url', function(){
            spyOn(dc, 'validNewSiteURL').and.returnValue(false);
            spyOn(dc, 'associateNewSite');
            var aEvent = angular.element.Event('keydown');
            aEvent.keyCode = 13;
            $("input").trigger(aEvent);
            dc.associateNewSiteHandleKey(aEvent);
            expect(dc.validNewSiteURL).toHaveBeenCalled();
            expect(dc.associateNewSite).not.toHaveBeenCalled();
        });

    });

    describe('associateNewSite', function(){
        beforeEach(function () {
            var ci = {
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
                        map_type: 'official',
                        site_map_id: '888'
                    },
                    {
                        external_id: 'https://x.y.z/999',
                        site_id: '999',
                        map_type: 'unofficial',
                        site_map_id: '999'
                    }
                ]
            };
            dc = $controller('SitesController', {$scope: scope});
            dc.courseInstance = ci;
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.flush(2);
        });

        it('should make the post call to associate a new site with the course instance', function(){
            dc.newCourseSiteURL = 'http://testing.com';
            dc.associateNewSite();
            $httpBackend.expectPOST(postSiteUrl)
                .respond(201, JSON.stringify({site_map_id: '777'}));
            $httpBackend.flush(1);
            siteList = [{external_id: 'https://x.y.z/888', site_id: '888', map_type: 'official', site_map_id: '888'},
                        {external_id: 'https://x.y.z/999', site_id: '999', map_type: 'unofficial', site_map_id: '999'},
                        {course_site_url: 'http://testing.com', map_type: 'official', site_map_id: '777'}
                        ];
            expect(dc.courseInstance.sites.length).toEqual(3);
            expect(dc.courseInstance.sites).toEqual(siteList);
        });

        it('should show an error message if the post fails', function(){
            dc.newCourseSiteURL = 'http://testing.com';
            dc.associateNewSite();
            $httpBackend.expectPOST(postSiteUrl)
                .respond(500, JSON.stringify({status: "invalid url"}));
            $httpBackend.flush(1);
            expect(dc.alerts.form.siteOperationFailed).toEqual({show: true, operation: 'associating', details: 'None'});
        });

    });

    xdescribe('dissociateSite', function(){
        beforeEach(function () {
            var ci = {
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
                        map_type: 'official',
                        course_site_url: 'https://x.y.z/888',
                        site_map_id: '888',
                    },
                    {
                        external_id: 'https://x.y.z/999',
                        site_id: '999',
                        map_type: 'unofficial',
                        course_site_url: 'https://x.y.z/999',
                        site_map_id: '999',

                    }
                ]
            };

            dc = $controller('SitesController', {$scope: scope});
            dc.courseInstance = ci;
            $httpBackend.expectGET(courseInstanceURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.expectGET(peopleURL).respond(200, JSON.stringify({status: "success"}));
            $httpBackend.flush(2);
        });

        it('should make the delete call to disasscociate a url with the course instance', function(){
            //delete by specifying the index
            siteListIndex = 1;
            original_count = dc.courseInstance.sites.length
            var siteURL = '';
            var site_map_id = '';
            dc.dissociateSite(siteListIndex);
            scope.$digest();// resolves modal init
            dc.confirmDissociateSiteModalInstance.close(siteURL, site_map_id);
            $httpBackend.expectDELETE(deleteSiteUrl).respond(204, {});
            $httpBackend.flush(1);
            //verify that the sites length is reduced by 1 after the delete
            expect(dc.courseInstance.sites.length).toEqual(original_count-1);
        });

        it('doesn\'t delete any sites if the process if canceled', function() {
            siteListIndex = 1;
            original_count = dc.courseInstance.sites.length;
            dc.dissociateSite(siteListIndex);
            scope.$digest();// resolves modal init
            dc.confirmDissociateSiteModalInstance.dismiss();
            //verify that the sites length is  unaffected.
            expect(dc.courseInstance.sites.length).toEqual(original_count);
        });

        it('should show an alert if the delete fails', function(){
            //delete by specifying the index
            siteListIndex = 1;
            original_count = dc.courseInstance.sites.length
            var siteURL = '';
            var site_map_id = '';
            dc.dissociateSite(siteListIndex);
            scope.$digest();//resolves modal
            dc.confirmDissociateSiteModalInstance.close(siteURL, site_map_id);
            $httpBackend.expectDELETE(deleteSiteUrl).respond(404, {});
            $httpBackend.flush(1);
            expect(dc.alerts.form.siteOperationFailed.show).toEqual(true);
            //validate that the sites length is unaffected due to a failure in delete
            expect(dc.courseInstance.sites.length).toEqual(original_count);
        });
    });
});
