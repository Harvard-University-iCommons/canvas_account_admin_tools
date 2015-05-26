var courseConclusionApp = angular.module('courseConclusionApp', []);

courseConclusionApp.controller('CourseConclusionController', function() {
    var cc = this;

    cc.schools = ['FAS', 'GSE', 'DCE'];
    cc.schoolProp = ""

    cc.term_temps = ['Spring 2015', 'Summer 2015', 'Fall 2015'];
    cc.terms = [];
    cc.termProp = "";

    cc.course_temps = ['Bio 101', 'Chem 100', 'Phys 102'];
    cc.courses = [];
    cc.courseProp = "";

    cc.fillTerms = function() {
        cc.terms = cc.term_temps.map(function(tt) {
                       return cc.schoolProp + " " + tt;
                   });
    };

    cc.fillCourses = function() {
        cc.courses = cc.course_temps.map(function(ct) {
                         return cc.termProp + " " + ct;
                     });
    }

});
