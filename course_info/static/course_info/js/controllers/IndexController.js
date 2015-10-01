(function(){
    /**
     * Angular controller for the home page of course_info.
     */
    angular.module('app').controller('IndexController', ['$scope', '$http', function($scope, $http){
        $scope.searchInProgress = false;
        $scope.useCannedData = false;

        $scope.courseInstanceToTable = function(course) {
            var cinfo = {};
            // todo: fixme, should be department not school
            cinfo['department'] = course.course ? course.course.school_id : '';
            cinfo['description'] = course.title;
            cinfo['year'] = course.term ? course.term.academic_year : '';
            cinfo['term'] = course.term ? course.term.display_name : '';
            // todo: fixme (show multiple)
            if (course.sites && course.sites.length > 0) {
                cinfo['site_id'] = course.sites[0].external_id;
                cinfo['site_url'] = course.sites[0].course_site_url;
            } else {
                cinfo['site_id'] = '';
                cinfo['site_url'] = '';
            }
            if (course.sites && course.sites.length > 0) {
                cinfo['code'] = (course.course.registrar_code_display
                + ' (' + course.course.course_id + ')').trim();
            } else {
                cinfo['code'] = '';
            }
            cinfo['cid'] = course.course_instance_id;
            if (course.secondary_xlist_instances && course.secondary_xlist_instances.length > 0) {
                cinfo['xlist_status'] = 'Primary';
            } else if (course.primary_xlist_instances && course.primary_xlist_instances.length > 0) {
                cinfo['xlist_status'] = 'Secondary';
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
                    emptyTable: 'There are no courses to display.'
                },
                order: [[6, 'asc']],  // order by course instance ID
                columns: [
                    {data: 'department'},
                    {data: 'description'},
                    {data: 'year'},
                    {data: 'term'},
                    {data: 'site_id'},  // todo: render with link
                    {data: 'code'},
                    {data: 'cid'},
                    {data: 'xlist_status'}  // todo: render with badge
                ]
            });
        };

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
        }];

        if ($scope.useCannedData) {
            $scope.courseInfo = $scope.canned_courses.map($scope.courseInstanceToTable);
            angular.element(document).ready($scope.initializeDatatable);
        } else {
            // Use for direct access to local (sslserver) rest api
            var url = 'https://localhost:8001/api/course/v2/course_instances/?format=json&school=hds';
            // Use for passthrough configured in secure.py (not working for me right now)
            //var url = 'https://localhost:8000/icommons_rest_api/api/course/v2/course_instances/?format=json&school=hds';
            $http.get(url).success(function (data, status, headers, config) {
                $scope.api_courses = data.results;

                // flatten for datatable and generate composite fields
                $scope.courseInfo = $scope.api_courses.map($scope.courseInstanceToTable);

                angular.element(document).ready($scope.initializeDatatable);
                }).error(function (data, status, headers, config) {
                    // todo: error handling
                });
        }
    }]);
})();
