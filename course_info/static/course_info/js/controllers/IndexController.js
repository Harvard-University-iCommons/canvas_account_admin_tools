(function(){
    /**
     * Angular controller for the home page of course_info.
     */
    angular.module('app').controller('IndexController', ['$scope', '$http', 'CourseInstance', function($scope, $http, CourseInstance){
        $scope.searchInProgress = false;
        $scope.useCannedData = false;
        $scope.queryString = '';
        $scope.courseInfo = null;
        $scope.searchEnabled = false;
        $scope.filtersApplied = false;
        $scope.filterOptions = {
            sites: [
                {key:'sites', value: 'all', name:'All courses', query: false, text: 'All courses <span class="caret"></span>'},
                {key:'sites', value: 'ws', name:'Only courses with sites', query: true, text: 'Only courses with sites <span class="caret"></span>'},
                {key:'sites', value: 'ns', name:'Only courses without sites', query: true, text: 'Only courses without sites <span class="caret"></span>'},
                {key:'sites', value: 'so', name:'Sites without attached courses', query: true, text: 'Sites without attached courses <span class="caret"></span>'},
                {key:'sites', value: 'ca', name:'Courses being synced to Canvas', query: true, text: 'Courses being synced to Canvas <span class="caret"></span>'}
            ],
            schools: JSON.parse(document.getElementById('schoolOptions').innerHTML),
            // todo: this wants to be handled like .schools
            terms: [
                {key:'term', value: 'all', name:'All terms', query: false, text: 'All terms <span class="caret"></span>'},
                {key:'term', value: 'su', name:'Summer', query: true, text: 'Summer <span class="caret"></span>'},
                {key:'term', value: 'fa', name:'Fall', query: true, text: 'Fall <span class="caret"></span>'},
                {key:'term', value: 'sp', name:'Spring', query: true, text: 'Spring <span class="caret"></span>'},
                {key:'term', value: 'fy', name:'Full Year', query: true, text: 'Full Year <span class="caret"></span>'},
                {key:'term', value: 'wi', name:'Winter', query: true, text: 'Winter <span class="caret"></span>'},
                {key:'term', value: 'ja', name:'July and August', query: true, text: 'July and August <span class="caret"></span>'},
                {key:'term', value: 'jj', name:'June and July', query: true, text: 'June and July <span class="caret"></span>'},
                {key:'term', value: 's2', name:'Spring 2', query: true, text: 'Spring 2<span class="caret"></span>'},
                {key:'term', value: 's1', name:'Spring 1', query: true, text: 'Spring 1<span class="caret"></span>'},
                {key:'term', value: 'f2', name:'Fall 2', query: true, text: 'Fall 2 <span class="caret"></span>'},
                {key:'term', value: 'f1', name:'Fall 1', query: true, text: 'Fall 1 <span class="caret"></span>'},
                {key:'term', value: 'july', name:'July', query: true, text: 'July <span class="caret"></span>'},
                {key:'term', value: 'au', name:'August', query: true, text: 'August <span class="caret"></span>'},
                {key:'term', value: 'june', name:'June', query: true, text: 'June <span class="caret"></span>'},
                {key:'term', value: 'fw', name:'Fall-Winter', query: true, text: 'Fall-Winter <span class="caret"></span>'},
                {key:'term', value: 'ws', name:'Winter-Spring', query: true, text: 'Winter-Spring <span class="caret"></span>'},
                {key:'term', value: 'ss', name:'Spring Saturday', query: true, text: 'Spring Saturday <span class="caret"></span>'},
                {key:'term', value: 'fs', name:'Fall Saturday', query: true, text: 'Fall Saturday <span class="caret"></span>'}
            ],
            // todo: this wants to be handled like .schools
            years: [
                {key:'academic_year', value: 'all', name:'All years', query: false, text: 'All years <span class="caret"></span>'},
            ]
        };
        var year = (new Date()).getFullYear();
        for (var i=year+1; i>year-4; i--) {
            $scope.filterOptions.years.push({key: 'academic_year', value: i+'', name: i+'', query: true, text: i+' <span class="caret"></span>'})
        }
        $scope.filters = {
            // default to first in list on load
            schools: $scope.filterOptions.schools[0],
            sites: $scope.filterOptions.sites[0],
            terms: $scope.filterOptions.terms[0],
            years: $scope.filterOptions.years[0]
        };

        $scope.updateFilter = function(filterKey, selectedValue) {
            $scope.filters[filterKey] = $scope.filterOptions[filterKey].filter(
                function(option){ return option.value == selectedValue})[0];
            $scope.checkIfFiltersApplied();
        };

        $scope.checkIfFiltersApplied = function() {
            for (var key in $scope.filters) {
                if ($scope.filters[key].query) {
                    $scope.filtersApplied = true;
                    break;
                }
            $scope.filtersApplied = false;
            }
        };

        $scope.checkIfSearchable = function() {
            $scope.searchEnabled = $scope.filtersApplied || $scope.queryString.trim() != '';
        };

        $scope.$watch('filtersApplied', $scope.checkIfSearchable);
        $scope.$watch('queryString', $scope.checkIfSearchable);

        $scope.courseInstanceToTable = function(course) {
            var cinfo = {};
            cinfo['description'] = course.title;
            cinfo['year'] = course.term ? course.term.academic_year : '';
            cinfo['term'] = course.term ? course.term.display_name : '';
            cinfo['sites'] = course.sites || [];
            cinfo['sites'].forEach(function (site) {
                site.site_id = site.external_id;
                if (site.site_id.indexOf('http') === 0) {
                    site.site_id = site.site_id.substr(site.site_id.lastIndexOf('/')+1);
                }
            });
            cinfo['sites'].sort(function(a,b) {
                return (a.external_id > b.external_id) ? 1 :
                           (b.external_id > a.external_id) ? -1 : 0;
            });
            if (course.course) {
                cinfo['code'] = (course.course.registrar_code_display
                + ' (' + course.course.course_id + ')').trim();
                cinfo['departments'] = course.course.departments || [];
                cinfo['departments'].forEach(function (department) {
                    department.name = department.name;
                });

            } else {
                cinfo['code'] = '';
                cinfo['departments'] = '';
            }
            cinfo['cid'] = course.course_instance_id;
            if (course.secondary_xlist_instances && course.secondary_xlist_instances.length > 0) {
                cinfo['xlist_status'] = 'Primary';
                cinfo['xlist_status_label'] = 'success';
            } else if (course.primary_xlist_instances && course.primary_xlist_instances.length > 0) {
                cinfo['xlist_status'] = 'Secondary';
                cinfo['xlist_status_label'] = 'info';
            } else {
                cinfo['xlist_status'] = '';
            }
            return cinfo;
        };

        $scope.initializeDatatable = function() {
            $scope.dataTable = $('#courseInfoDT').DataTable({
                data: $scope.courseInfo,
                dataSrc: '',  // data is an array
                // todo: p_r_ocessing?...
                dom: '<<t>ip>',
                language: {
                    info: 'Showing _START_ to _END_ of _TOTAL_ courses',
                    emptyTable: 'There are no courses to display.',
                    // datatables-bootstrap js adds glyphicons, so remove
                    // default Previous/Next text and don't add &laquo; or
                    // &raquo; as in that case the chevrons will be repeated
                    paginate: {
                        previous: '',
                        next: ''
                    }
                },
                order: [[6, 'asc']],  // order by course instance ID
                columns: [
                    {render: function(data, type, row, meta) {
                        var depts = row.departments.map(function(department) {
                            return department.name;
                        });
                        return depts;
                    }},
                    {data: 'description'},
                    {data: 'year'},
                    {data: 'term'},
                    {render: function(data, type, row, meta) {
                        var sites = row.sites.map(function(site) {
                            return '<a href="' + site.course_site_url + '">'
                                       + site.site_id + '</a>';
                        });
                        return sites.join(', ');
                    }},
                    {data: 'code'},
                    {data: 'cid'},
                    {data: null, render: function(data, type, full, meta) {
                        if (data.xlist_status != '') {
                            return '<span class="label label-'
                                + data.xlist_status_label + '">'
                                + data.xlist_status + '</span>';
                        } else {
                            return data.xlist_status;
                        }
                    }}
                ]
            });
        };

        angular.element(document).ready($scope.initializeDatatable);

        $scope.updateData = function(newData) {
            if (newData) {
                $scope.dataTable.clear();
                $scope.dataTable.rows.add(newData);
                $scope.dataTable.draw();
            }
        };

        $scope.$watch('courseInfo', $scope.updateData);

        $scope.canned_courses = [{
            "course_instance_id": 339009,
            "course": {
                "url": "https://icommons.harvard.edu/api/course/v2/courses/86374/",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/ksg/",
                "registrar_code": "HKSEEEL1402",
                "registrar_code_display": "",
                "course_id": 86374,
                "school_id": "ksg"
            },
            "term": {
                "url": "https://icommons.harvard.edu/api/course/v2/terms/4968/",
                "academic_year": "2014",
                "display_name": "Spring 2014",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/ksg/",
                "school_id": "ksg",
                "term_id": 4968,
                "term_code": 2,
                "term_name": "Spring"
            },
            "sites": [
                {
                    "external_id": "k102751",
                    "site_type_id": "isite",
                    "course_site_url": "http://isites.harvard.edu/k102751",
                    "url": "https://icommons.harvard.edu/api/course/v2/course_sites/189769/"
                }
            ],
            "url": "https://icommons.harvard.edu/api/course/v2/course_instances/339009/",
            "section": "",
            "title": "Emerging Leaders",
            "short_title": "",
            "sub_title": "",
            "location": "",
            "meeting_time": "",
            "exam_group": "",
            "instructors_display": "",
            "description": "",
            "notes": "",
            "prereq": "",
            "course_type": "",
            "xreg_flag": 0,
            "xlist_flag": 0,
            "enrollment_limit_flag": 0,
            "audit_flag": 0,
            "undergraduate_credit_flag": 0,
            "graduate_credit_flag": 0,
            "offered_flag": 1,
            "exclude_from_isites": "0",
            "exclude_from_catalog": "1",
            "exclude_from_coop": null,
            "credits": "",
            "exam_date": null,
            "exam_date_description": "",
            "xlist_description": "",
            "xreg_description": "",
            "next_offer_year": null,
            "info_url": "",
            "enrollment_limit": "",
            "xreg_instructor_sig_reqd": "1",
            "xreg_grading_options": "",
            "sync_to_canvas": false,
            "canvas_course_id": null,
            "secondary_xlist_instances": [],
            "primary_xlist_instances": []
        }, {
            "course_instance_id": 339009,
            "course": {
                "url": "https://icommons.harvard.edu/api/course/v2/courses/86374/",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/ksg/",
                "registrar_code": "HKSEEEL1402",
                "registrar_code_display": "",
                "course_id": 86374,
                "school_id": "ksg"
            },
            "term": {
                "url": "https://icommons.harvard.edu/api/course/v2/terms/4968/",
                "academic_year": "2014",
                "display_name": "Spring 2014",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/ksg/",
                "school_id": "ksg",
                "term_id": 4968,
                "term_code": 2,
                "term_name": "Spring"
            },
            "sites": [
                {
                    "external_id": "k102751",
                    "site_type_id": "isite",
                    "course_site_url": "http://isites.harvard.edu/k102751",
                    "url": "https://icommons.harvard.edu/api/course/v2/course_sites/189769/"
                }
            ],
            "url": "https://icommons.harvard.edu/api/course/v2/course_instances/339009/",
            "section": "",
            "title": "Emerging Leaders",
            "short_title": "",
            "sub_title": "",
            "location": "",
            "meeting_time": "",
            "exam_group": "",
            "instructors_display": "",
            "description": "",
            "notes": "",
            "prereq": "",
            "course_type": "",
            "xreg_flag": 0,
            "xlist_flag": 0,
            "enrollment_limit_flag": 0,
            "audit_flag": 0,
            "undergraduate_credit_flag": 0,
            "graduate_credit_flag": 0,
            "offered_flag": 1,
            "exclude_from_isites": "0",
            "exclude_from_catalog": "1",
            "exclude_from_coop": null,
            "credits": "",
            "exam_date": null,
            "exam_date_description": "",
            "xlist_description": "",
            "xreg_description": "",
            "next_offer_year": null,
            "info_url": "",
            "enrollment_limit": "",
            "xreg_instructor_sig_reqd": "1",
            "xreg_grading_options": "",
            "sync_to_canvas": false,
            "canvas_course_id": null,
            "secondary_xlist_instances": [],
            "primary_xlist_instances": []
        }, {
            "course_instance_id": 336460,
            "course": {
                "url": "https://icommons.harvard.edu/api/course/v2/courses/85149/",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/hu/",
                "registrar_code": "hktest103",
                "registrar_code_display": "",
                "course_id": 85149,
                "school_id": "hu"
            },
            "term": {
                "url": "https://icommons.harvard.edu/api/course/v2/terms/5048/",
                "academic_year": "2014",
                "display_name": "Spring 2014",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/hu/",
                "school_id": "hu",
                "term_id": 5048,
                "term_code": 2,
                "term_name": "Spring"
            },
            "sites": [
                {
                    "external_id": "k100795",
                    "site_type_id": "isite",
                    "course_site_url": "http://isites.harvard.edu/k100795",
                    "url": "https://icommons.harvard.edu/api/course/v2/course_sites/187938/"
                }
            ],
            "url": "https://icommons.harvard.edu/api/course/v2/course_instances/336460/",
            "section": "",
            "title": "Hiu Kei Sample Course (k100795) -Pulled from 'Course Title' Field ",
            "short_title": "",
            "sub_title": "",
            "location": "",
            "meeting_time": "",
            "exam_group": "",
            "instructors_display": "",
            "description": "<p>How can the practice of urban planning and design creatively engage communities to address the immediate and long-term challenges posed by climate variability and environmental change? The course will discuss environmental problems facing cities around the world through the lens of environmental equity, and provide an introduction to the ideas and information necessary to integrate ecological viability with the other primary concerns of planners and designers; namely, social justice, healthy communities and economic development.</p> <br /> <br /> <p>&nbsp;</p> <br /> <p>The course will explore the historical roots of urban environmental planning and environmental justice as a social movement, examine theories that have developed to encourage the restructuring and redesign of land use patterns, environmental regulation and systems of production, and critically review some of the methods and processes of planning in light of disproportionate impacts of environmental burdens and exposures to hazards on low-income and communities of color. Efforts to foster environmental equity have emphasized community-based approaches, and we will discuss the strategies, scholarship and case examples of collaborative, community planning and participatory action research.</p> <br /> <br /> <p>&nbsp;</p> <br /> <p>The objectives of the course are twofold: to understand the methods and practical processes of urban environmental planning with cognizance to their social justice dimensions, <i>and</i> to critically analyze existing plans and planning processes in terms of their ability to help urban populations cope with a changing environment and atmosphere. The course seeks to provide an overview of the major concepts, actors, and methods (such as risk assessment and environmental review) involved in or used in the decision-making context, while emphasizing innovation in planning and design to address complex and related problems in land-use, air quality, watershed protection, waste disposal, climate change, and environmental health.</p> <br /> <p><i>&nbsp;</i></p> <br /> <p><i>Class format and requirements:</i> The course will involve a mix of lectures and discussion, with one or two in-class exercises. The course is open to all GSD disciplines. Students will develop, present and write about an individual research project, with the opportunity to collaborate and develop research on a current environmental planning effort in Cambridge. Work will be evaluated based on short response papers, discussion of class readings, the quality of overall class participation, and the final research presentation and report.</p> <br />",
            "notes": "",
            "prereq": "",
            "course_type": "",
            "xreg_flag": 0,
            "xlist_flag": 0,
            "enrollment_limit_flag": 0,
            "audit_flag": 0,
            "undergraduate_credit_flag": 0,
            "graduate_credit_flag": 0,
            "offered_flag": 1,
            "exclude_from_isites": "0",
            "exclude_from_catalog": "1",
            "exclude_from_coop": null,
            "credits": "",
            "exam_date": null,
            "exam_date_description": "",
            "xlist_description": "",
            "xreg_description": "",
            "next_offer_year": null,
            "info_url": "",
            "enrollment_limit": "",
            "xreg_instructor_sig_reqd": "1",
            "xreg_grading_options": "",
            "sync_to_canvas": true,
            "canvas_course_id": 308,
            "secondary_xlist_instances": [],
            "primary_xlist_instances": []
        }, {
            "course_instance_id": 334017,
            "course": {
                "url": "https://icommons.harvard.edu/api/course/v2/courses/14548/",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/hds/",
                "registrar_code": "104464",
                "registrar_code_display": "HDS 2674",
                "course_id": 14548,
                "school_id": "hds"
            },
            "term": {
                "url": "https://icommons.harvard.edu/api/course/v2/terms/4890/",
                "academic_year": "2014",
                "display_name": "Spring 2014",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/hds/",
                "school_id": "hds",
                "term_id": 4890,
                "term_code": 2,
                "term_name": "Spring"
            },
            "sites": [
                {
                    "external_id": "k99799",
                    "site_type_id": "isite",
                    "course_site_url": "http://isites.harvard.edu/k99799",
                    "url": "https://icommons.harvard.edu/api/course/v2/course_sites/187016/"
                }
            ],
            "url": "https://icommons.harvard.edu/api/course/v2/course_instances/334017/",
            "section": "",
            "title": "Kant: Seminar",
            "short_title": "",
            "sub_title": "",
            "location": "Divinity Hall, Room 211",
            "meeting_time": "Friday 12:00pm - 2:00pm",
            "exam_group": "",
            "instructors_display": "David C. Lamberth",
            "description": "A close reading of major works of Kant relevant to theology and philosophy of religion. The seminar will focus on issues such as the nature and limits of reason, the concepts of freedom, morality and faith, and the idea of God. Prerequisite: advanced work in theology or philosophy of religion. Offered jointly with the Faculty of Arts and Sciences as Religion 2542.",
            "notes": "",
            "prereq": "",
            "course_type": "Seminar",
            "xreg_flag": 1,
            "xlist_flag": 1,
            "enrollment_limit_flag": 1,
            "audit_flag": 0,
            "undergraduate_credit_flag": 0,
            "graduate_credit_flag": 1,
            "offered_flag": 1,
            "exclude_from_isites": "0",
            "exclude_from_catalog": "0",
            "exclude_from_coop": 0,
            "credits": "0.50",
            "exam_date": null,
            "exam_date_description": "",
            "xlist_description": "",
            "xreg_description": "",
            "next_offer_year": null,
            "info_url": "http://www.hds.harvard.edu/academics/courses/course-detail.cfm?CrsNumber=2674&section=01&term=SPRING&year=2014",
            "enrollment_limit": "12",
            "xreg_instructor_sig_reqd": "1",
            "xreg_grading_options": "letter/ordinal|sat/unsat|audit",
            "sync_to_canvas": false,
            "canvas_course_id": null,
            "secondary_xlist_instances": [
                "https://icommons.harvard.edu/api/course/v2/course_instances/324053/"
            ],
            "primary_xlist_instances": []
        }, {
            "course_instance_id": 324053,
            "course": {
                "url": "https://icommons.harvard.edu/api/course/v2/courses/60154/",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/colgsas/",
                "registrar_code": "119369",
                "registrar_code_display": "119369",
                "course_id": 60154,
                "school_id": "colgsas"
            },
            "term": {
                "url": "https://icommons.harvard.edu/api/course/v2/terms/4468/",
                "academic_year": "2013",
                "display_name": "Spring 2013-2014",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/colgsas/",
                "school_id": "colgsas",
                "term_id": 4468,
                "term_code": 2,
                "term_name": "Spring"
            },
            "sites": [],
            "url": "https://icommons.harvard.edu/api/course/v2/course_instances/324053/",
            "section": "",
            "title": "Religion 2542",
            "short_title": "RELIGION 2542",
            "sub_title": "Kant: Seminar",
            "location": "",
            "meeting_time": "Friday 12:00pm - 2:00pm",
            "exam_group": "5,6",
            "instructors_display": "David Lamberth (Divinity School)",
            "description": "A close reading of major works of Kant relevant to theology and philosophy of religion. The seminar focuses on issues such as the nature and limits of reason, the concepts of freedom, morality and faith, and the idea of God.",
            "notes": "Offered jointly with the Divinity School as 2674.",
            "prereq": "Advanced work in theology or philosophy of religion.",
            "course_type": "Seminar",
            "xreg_flag": 1,
            "xlist_flag": 0,
            "enrollment_limit_flag": 0,
            "audit_flag": 0,
            "undergraduate_credit_flag": 0,
            "graduate_credit_flag": 1,
            "offered_flag": 1,
            "exclude_from_isites": "0",
            "exclude_from_catalog": "1",
            "exclude_from_coop": 0,
            "credits": "Half course",
            "exam_date": null,
            "exam_date_description": "",
            "xlist_description": "",
            "xreg_description": "",
            "next_offer_year": null,
            "info_url": "",
            "enrollment_limit": "12",
            "xreg_instructor_sig_reqd": "1",
            "xreg_grading_options": "letter/ordinal",
            "sync_to_canvas": false,
            "canvas_course_id": null,
            "secondary_xlist_instances": [],
            "primary_xlist_instances": [
                "https://icommons.harvard.edu/api/course/v2/course_instances/334017/"
            ]
        }, {
            "course_instance_id": 291651,
            "course": {
                "url": "https://icommons-rest-api.dev.tlt.harvard.edu/api/course/v2/courses/65025/",
                "school": "https://icommons-rest-api.dev.tlt.harvard.edu/api/course/v2/schools/colgsas/",
                "registrar_code": "111104",
                "registrar_code_display": "1914",
                "course_id": 65025,
                "school_id": "colgsas"
            },
            "term": {
                "url": "https://icommons-rest-api.dev.tlt.harvard.edu/api/course/v2/terms/3221/",
                "academic_year": "2011",
                "display_name": "Fall 2011-2012",
                "school": "https://icommons-rest-api.dev.tlt.harvard.edu/api/course/v2/schools/colgsas/",
                "school_id": "colgsas",
                "term_id": 3221,
                "term_code": 1,
                "term_name": "Fall"
            },
            "sites": {
                "course_site_url": "http://isites.harvard.edu/k79918"
            },
            "url": "https://icommons-rest-api.dev.tlt.harvard.edu/api/course/v2/course_instances/291651/",
            "section": "",
            "title": "History 82l",
            "short_title": "HIST 82l",
            "sub_title": "The French Revolution",
            "location": "",
            "meeting_time": "Wednesday 2:00pm - 4:00pm",
            "exam_group": "7,8",
            "instructors_display": "Patrice Higonnet 2730 (on leave spring term)",
            "description": "The history of Jacobinism during the French Revolution.",
            "notes": "",
            "prereq": "",
            "course_type": "Research Seminar",
            "xreg_flag": 1,
            "xlist_flag": 0,
            "enrollment_limit_flag": 0,
            "audit_flag": 0,
            "undergraduate_credit_flag": 1,
            "graduate_credit_flag": 0,
            "offered_flag": 1,
            "exclude_from_isites": "0",
            "exclude_from_catalog": "0",
            "exclude_from_coop": null,
            "credits": "Half course",
            "exam_date": null,
            "exam_date_description": "",
            "xlist_description": "",
            "xreg_description": "",
            "next_offer_year": null,
            "info_url": "",
            "enrollment_limit": "15",
            "xreg_instructor_sig_reqd": "1",
            "xreg_grading_options": "letter/ordinal",
            "sync_to_canvas": 0,
            "canvas_course_id": null,
            "secondary_xlist_instances": [],
            "primary_xlist_instances": []
        }, {
            "course_instance_id": 357547,
            "course": {
                "url": "https://icommons.harvard.edu/api/course/v2/courses/87208/",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/colgsas/",
                "registrar_code": "110382",
                "registrar_code_display": "110382",
                "course_id": 87208,
                "school_id": "colgsas"
            },
            "term": {
                "url": "https://icommons.harvard.edu/api/course/v2/terms/5928/",
                "academic_year": "2015",
                "display_name": "Fall 2015-2016",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/colgsas/",
                "school_id": "colgsas",
                "term_id": 5928,
                "term_code": 1,
                "term_name": "Fall"
            },
            "sites": [
                {
                    "external_id": "https://canvas.harvard.edu/courses/3232",
                    "site_type_id": "external",
                    "course_site_url": "https://canvas.harvard.edu/courses/3232",
                    "url": "https://icommons.harvard.edu/api/course/v2/course_sites/201661/"
                },
                {
                    "external_id": "k113141",
                    "site_type_id": "isite",
                    "course_site_url": "http://isites.harvard.edu/k113141",
                    "url": "https://icommons.harvard.edu/api/course/v2/course_sites/205889/"
                }
            ],
            "url": "https://icommons.harvard.edu/api/course/v2/course_instances/357547/",
            "section": "001",
            "title": "SCILIVSY 26",
            "short_title": "SCILIVSY 26",
            "sub_title": "The Toll of Infection: Understanding Disease in Scientific, Social, and Cultural Contexts",
            "location": "Holden Chapel Classroom (FAS)",
            "meeting_time": "Monday, Wednesday 1:00pm - 2:29pm",
            "exam_group": "FAS08_I",
            "instructors_display": "Donald A. Goldmann (Harvard School of Public Health)",
            "description": "This course will review the devastating impact of representative infectious diseases on wars, politics, economics, religion, public health, and society as reflected in history, literature, and the arts. We will study how infections spawned revolutionary epidemiologic and scientific advances in detection, treatment, and prevention. We will address the gaps between discovery and implementation, including ethical, social, economic, and health systems barriers to progress. We will confront challenges posed by microbial mutation (e.g., antibiotic resistance, evasion of immunity, and adaptation of animal viruses to humans). By weaving together knowledge from science and the humanities, students will understand the historical and contemporary impact of infections and potential solutions to the challenges they pose.",
            "notes": "If student interest exceeds the course limit, a random lottery will be conducted. To enter the lottery, you must add the course to the Study Card and explicitly request enrollment permission when prompted. Instructor permission will be granted to only those admitted by the lottery; all students will be notified of their results. See the course website for more details.",
            "prereq": "",
            "course_type": "Lecture",
            "xreg_flag": 1,
            "xlist_flag": 0,
            "enrollment_limit_flag": 0,
            "audit_flag": 0,
            "undergraduate_credit_flag": 1,
            "graduate_credit_flag": 0,
            "offered_flag": 1,
            "exclude_from_isites": "0",
            "exclude_from_catalog": "0",
            "exclude_from_coop": null,
            "credits": "4",
            "exam_date": "2015-12-15",
            "exam_date_description": "",
            "xlist_description": "",
            "xreg_description": "",
            "next_offer_year": null,
            "info_url": "",
            "enrollment_limit": "60",
            "xreg_instructor_sig_reqd": "1",
            "xreg_grading_options": "letter/ordinal",
            "sync_to_canvas": true,
            "canvas_course_id": 3232,
            "secondary_xlist_instances": [],
            "primary_xlist_instances": []
        }, {
            "course_instance_id": 348897,
            "course": {
                "url": "https://icommons.harvard.edu/api/course/v2/courses/66353/",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/hds/",
                "registrar_code": "103794",
                "registrar_code_display": "HDS 1551",
                "course_id": 66353,
                "school_id": "hds"
            },
            "term": {
                "url": "https://icommons.harvard.edu/api/course/v2/terms/5511/",
                "academic_year": "2014",
                "display_name": "Fall 2014",
                "school": "https://icommons.harvard.edu/api/course/v2/schools/hds/",
                "school_id": "hds",
                "term_id": 5511,
                "term_code": 1,
                "term_name": "Fall"
            },
            "sites": [
                {
                    "external_id": "k105393",
                    "site_type_id": "isite",
                    "course_site_url": "http://isites.harvard.edu/k105393",
                    "url": "https://icommons.harvard.edu/api/course/v2/course_sites/192520/"
                },
                {
                    "external_id": "https://canvas.harvard.edu/courses/816",
                    "site_type_id": "external",
                    "course_site_url": "https://canvas.harvard.edu/courses/816",
                    "url": "https://icommons.harvard.edu/api/course/v2/course_sites/192561/"
                }
            ],
            "url": "https://icommons.harvard.edu/api/course/v2/course_instances/348897/",
            "section": "",
            "title": "Greek Exegesis of 1 Corinthians",
            "short_title": "",
            "sub_title": "",
            "location": "Divinity Hall, Room 106",
            "meeting_time": "Wednesday 1:00pm - 3:00pm",
            "exam_group": "",
            "instructors_display": "Laura Salah Nasrallah",
            "description": "The course is devoted to close reading and interpretation of 1 Corinthians. Discussion of the Greek text of 1 Corinthians will focus on literary style, use of rhetoric, philology, and the social and theological issues of the text. This course also fulfills the study of fourth semester Greek. Note: Course has additional hour to be arranged. Offered jointly with the Faculty of Arts and Sciences as Religion 1441.",
            "notes": "",
            "prereq": "",
            "course_type": "Lecture",
            "xreg_flag": 1,
            "xlist_flag": 1,
            "enrollment_limit_flag": 0,
            "audit_flag": 0,
            "undergraduate_credit_flag": 0,
            "graduate_credit_flag": 1,
            "offered_flag": 1,
            "exclude_from_isites": "0",
            "exclude_from_catalog": "0",
            "exclude_from_coop": 0,
            "credits": "0.50",
            "exam_date": null,
            "exam_date_description": "",
            "xlist_description": "",
            "xreg_description": "",
            "next_offer_year": null,
            "info_url": "http://div.hds.harvard.edu/academics/courses/course-detail.cfm?CrsNumber=1551&section=01&term=FALL&year=2014",
            "enrollment_limit": "No",
            "xreg_instructor_sig_reqd": "0",
            "xreg_grading_options": "letter/ordinal|sat/unsat|audit",
            "sync_to_canvas": true,
            "canvas_course_id": 816,
            "secondary_xlist_instances": [],
            "primary_xlist_instances": []
        }];

        $scope.searchCourseInstances = function() {
            $scope.searchInProgress = true;
            if ($scope.useCannedData) {
                $scope.courseInfo = $scope.canned_courses.map($scope.courseInstanceToTable);
                $scope.searchInProgress = false;
            } else {
                // Use for direct access to local (sslserver) rest api
                // * ensure authorization header code in app.js is active
                //var url = 'https://localhost:8001/api/course/v2/course_instances/?format=json';

                // Use for passthrough configured in secure.py
                // * also comment-out authorization header code in app.js
                var queryParameters = {};
                if ($scope.queryString.trim() != '') {
                    queryParameters.search = $scope.queryString.trim();
                }
                if ($scope.filtersApplied) {
                    for (var key in $scope.filters) {
                        var f = $scope.filters[key];
                        if (f.query) { queryParameters[f.key] = f.value; }
                    }
                }
                $scope.api_course_results = CourseInstance.query(queryParameters, function() {
                    $scope.api_courses = $scope.api_course_results.results;
                    $scope.courseInfo = $scope.api_courses.map($scope.courseInstanceToTable);
                    $scope.searchInProgress = false;
                });
            }
        }
    }]);
})();
