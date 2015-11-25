describe('Unit testing PeopleController', function() {
    var $controller, $rootScope, $routeParams, courseInstances, $compile, djangoUrl;
    var controller, scope;
    beforeEach(function() {
        module('CourseInfo');
        inject(function(_$controller_, _$rootScope_, _$routeParams_, _courseInstances_, _$compile_, _djangoUrl_) {
            $controller = _$controller_;
            $rootScope = _$rootScope_;
            $routeParams = _$routeParams_;
            courseInstances = _courseInstances_;
            $compile = _$compile_;
            djangoUrl = _djangoUrl_;
        });
        scope = $rootScope.$new();
        $routeParams.course_instance_id = 1234567890;
        controller = $controller('PeopleController', {$scope: scope });
    });

    // sanity check the tests
    it('should inject the providers we requested', function() {
        [$controller, $rootScope, $routeParams, courseInstances, $compile, djangoUrl].forEach(function(thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    // this controller doesn't do anything besides setting up datatables config
    // on the scope.
    describe('$scope setup', function() {
        it('should set the course instance id', function() {
            expect(scope.course_instance_id).toEqual($routeParams.course_instance_id);
        });

        it('should set the title when courseInstances is full', function() {
            expect(scope.title).not.toBeUndefined();
            expect(scope.title).not.toBeNull();
        });

        it('should set the title when courseInstances is empty', function() {
            expect(scope.title).not.toBeUndefined();
            expect(scope.title).not.toBeNull();
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
});
