describe('Unit testing CourseInstancesService', function() {
    beforeEach(module('CourseInfo'));

    var courseInstances;
    beforeEach(inject(function($injector) {
        courseInstances = $injector.get('courseInstances');
    }));

    // sanity check the test framework
    it('should retrieve the service', function() {
        expect(courseInstances).not.toBeUndefined();
        expect(courseInstances).not.toBeNull();
    });

    // it's really just a place to stash an object
    it('should return the same object you stored in it', function() {
        var testInstances = {test: 'test'};
        courseInstances.instances = testInstances;
        expect(courseInstances.instances).toEqual(testInstances);
    });
});
