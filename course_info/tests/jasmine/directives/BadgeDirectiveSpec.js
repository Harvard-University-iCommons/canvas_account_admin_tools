describe('Unit testing BadgeDirective', function() {
    beforeEach(module('CourseInfo'));
    beforeEach(module('templates'));

    var $compile, $rootScope, $templateCache;
    beforeEach(inject(function(_$compile_, _$rootScope_, _$templateCache_) {
        $compile = _$compile_;
        $rootScope = _$rootScope_;
        $templateCache = _$templateCache_;
    }));

    // sanity check the test framework
    it('should inject the providers we requested', function() {
        [$compile, $rootScope].forEach(function(thing) {
            expect(thing).not.toBeUndefined();
            expect(thing).not.toBeNull();
        });
    });

    // these are just copied from BadgeDirective.js, and should be kept in sync.
    // note that NOPE is added to test the handling of roles not in roleToBadge.
    var roleToBadge = {
        CLASPART: 'HUID',
        COUNTWAY: 'LIBRARY',
        EMPLOYEE: 'HUID',
        STUDENT: 'HUID',
        WIDENER: 'LIBRARY',
        XIDHOLDER: 'XID',
        NOPE: 'OTHER',
    };
    var badgeToClass = {
        HUID: 'label-danger',
        XID: 'label-primary',
        LIBRARY: 'label-success',
        OTHER: 'label-warning',
    };

    for (role in roleToBadge) {
        var expectedBadge = roleToBadge[role];
        var expectedClass = badgeToClass[expectedBadge];

        it('Returns the expected badge for ' + role, function() {
            var element = $compile('<badge role="' + role + '"></badge>')($rootScope);
            $rootScope.$digest();
            expect(element.find('span').text()).toBe(expectedBadge);
            expect(element.find('span').prop('class')).toContain(expectedClass);
        });
    }
});
