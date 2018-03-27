(function initCreateNewCourseController() {
    /**
     * Angular controller for the create new course page.
     */
    var app = angular.module('app');
    app.controller('CreateNewCourseController', CreateNewCourseController);

    function CreateNewCourseController($scope, $http, $uibModal, $log,
                                       djangoUrl, $q, school) {
        var validCourseCodeRegex = new RegExp('^[a-zA-Z0-9\-_\.]+$');
        $scope.course = {
            code: '',
            codeString: '',
            codeType: '',
            shortTitle: '',
            term: null,
            title: ''
        };
        $scope.courseCreationInProgress = false;
        $scope.courseCreationSuccessful = false;
        $scope.templateUsed = false;
        $scope.departments = {};
        $scope.errorCreatingCourse = null;
        $scope.errorInCourseCode = null;
        $scope.errorMessageSupport = "Please contact tlt_support@harvard.edu.";
        $scope.existingCourse = null;
        $scope.existingCourseModal = null;
        $scope.existingSections = [];
        $scope.newCourseInstance = null;
        $scope.school = school;
        $scope.sectionId = '';
        $scope.selectedTerm = null;
        $scope.terms = [];
        $scope.isBlueprint = false;

        $scope.setCourseCode = function() {
            if ($scope.course.codeType
                    && validCourseCodeRegex.test($scope.course.codeString)) {
                $scope.course.code = $scope.course.codeType + '-'
                    + $scope.course.codeString;
                $scope.errorInCourseCode = null;
            } else if ($scope.course.codeString.trim().length == 0) {
                $scope.course.code = '';
                $scope.errorInCourseCode = null;
            } else {
                $scope.course.code = '';
                $scope.errorInCourseCode = 'Please only include ' +
                  'alphanumeric characters and the following symbols in the ' +
                  'course code: Period [ . ] Dash [ - ] Underscore [ _ ]. ' +
                  'Spaces are not allowed.';
            }
        };

        // Handles the blueprint checkbox change event
        // If checked, set the courses code type to have the prefix BLU
        // On an uncheck, set the code type back to the initial option value of ILE
        $scope.blueprintBoxChange = function() {
            if($scope.isBlueprint) {
                $scope.course.codeType = 'BLU'
            } else {
                $scope.course.codeType = 'ILE'
            }
            $scope.setCourseCode()
        };

        $scope.createButtonEnabled = function(){
            if ($scope.course.term && $scope.course.code
                && $scope.course.title && !$scope.courseCreationInProgress) {
                return true;
            } else {
                return false;
            }
        };

        /*
         * The approach for the section field in the database is to use
         * incrementing numbers, even though the field is defined as a
         * string.  The numbers are eventually 0-padded to a width of 3.
         * Note that if we ever need 1000 courses, there may be some
         * unexpected behavior.
         */
        $scope.getNextSectionId = function(sectionList){
            if (sectionList.length > 0){
                // NOTE: sectionList is $scope.existingSections, so this
                //       is mutating a scope variable.  nothing else uses
                //       it, though, so it's not worth making a local copy.
                sectionList.sort();

                // be paranoid about the possibility of non-numeric sections
                for (var i=sectionList.length-1; i>=0; i--) {
                    var maxId = parseInt(sectionList[i]);
                    if (!Number.isNaN(maxId)) {
                        // poor man's zero-fill, since js hates productivity.
                        // prepend the next id with 0s, then slice off the end
                        return ("000" + (maxId+1)).slice(-3);
                    }
                }
            }

            // if there's no existing sections, or none of them are numeric,
            // start numbering at 1.
            return '001';
        };

        $scope.handleCreate = function () {
            $scope.existingSections = [];
            $scope.courseCreationInProgress = true;

            $scope.getExistingCourse().then(
                function determineCourseToCreate() {
                    if ($scope.existingCourse == null) {
                        // no course exists, go ahead and create the course
                        // record and a new course instance
                        $scope.createCourseAndInstance();
                    } else if ($scope.existingSections.length == 0) {
                        // course exists, but no course instances exist for the
                        // course in this term; go ahead and create a new course
                        // instance
                        $scope.prepCourseSectionAndCreateCourse();
                    } else {
                        // at least one course instance already exists for this
                        // course in this term; prompt user to continue
                        // via modal dialog
                        $scope.existingCourseModal = $uibModal.open({
                            templateUrl: 'partials/create_new_course_existing_course_modal.html'
                        });

                        // if they confirm, then create a new course instance
                        $scope.existingCourseModal.result.then(
                            $scope.prepCourseSectionAndCreateCourse,
                            $scope.cancelCreateNewCourseInstance
                        ).finally(
                            function removeModal() {
                                $scope.existingCourseModal = null;
                            }
                        );
                    }
                }, $scope.cancelCreateNewCourseInstance);
        };

        $scope.cancelCreateNewCourseInstance = function () {
          $scope.courseCreationInProgress = false;
        };

        $scope.getExistingCourse = function() {
            return $q(function(resolve, reject) {
                var url = djangoUrl.reverse(
                    'icommons_rest_api_proxy', ['api/course/v2/courses/']);
                var config = {params: {
                    limit: 1000,  // TODO: api read-all-data;
                    registrar_code: $scope.course.code,
                    school: $scope.school.id
                }};
                $http.get(url, config).then(
                    function determineExistingCourse(response) {
                        // check if a course already exists
                        if (response.data.results.length > 0) {
                            $scope.existingCourse = response.data.results[0];
                            if (response.data.results.length > 1) {
                                $log.warn('Multiple courses found with ' +
                                    'registrar code ' + $scope.course.code +
                                    ', using first course. All results: '
                                    + JSON.stringify(response.data.results));
                            }
                            // this will resolve getExistingCourse() when
                            // getExistingCourseInstances() resolves
                            resolve($scope.getExistingCourseInstances());
                        } else {
                            $scope.existingCourse = null;
                            resolve();
                        }
                    }, function getExistingCourseFailed(response) {
                        $scope.handleAjaxErrorWithMessage(response);
                        reject('Error looking up course information.');
                    })
            });
        };

        $scope.getExistingCourseInstances = function() {
            // Section name has to be unique per course per term, so collect all
            // existing section names for course and term
            return $q(function(resolve, reject) {
                var url = djangoUrl.reverse(
                    'icommons_rest_api_proxy',
                    ['api/course/v2/course_instances/']);
                var config = {
                    params: {
                        course__course_id: $scope.existingCourse.course_id,
                        limit: 1000,  // TODO: api read-all-data;
                        term: $scope.course.term
                    }
                };

                $http.get(url, config).then(
                    function getSections(response) {
                        $scope.existingSections = response.data.results.map(
                            function extractSection(courseInstance) {
                                return courseInstance.section;
                            });
                        resolve();
                    }, function getExistingCourseInstancesFailed(response) {
                        $scope.handleAjaxErrorWithMessage(response);
                        reject('Error looking up course information.');
                    }
                );
            });
        };

        $scope.prepCourseSectionAndCreateCourse = function() {
            $scope.course.section = $scope.getNextSectionId(
                $scope.existingSections);
            $scope.createCourseInstance($scope.existingCourse.course_id);
        };

        $scope.createCourseInstance = function(course_id){
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                ['api/course/v2/course_instances/']);
            var data = {
                course: course_id,
                exclude_from_catalog: 1,
                section: $scope.course.section,
                short_title: $scope.course.shortTitle,
                sync_to_canvas: 0,
                term: $scope.course.term,
                title: $scope.course.title
            };
            $http.post(url, data).then(
                function finalizeCreateCourseInstance(response){
                    $scope.newCourseInstance = response.data;
                    $scope.createCanvasCourse();
                }, $scope.handleAjaxErrorWithMessage
            );
        };

        $scope.createCourseAndInstance = function(){
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                ['api/course/v2/courses/']);
            var departmentId = $scope.departments[$scope.course.codeType.toLowerCase()];
            var data = {
                registrar_code: $scope.course.code,
                registrar_code_display: $scope.course.code,
                school: $scope.school.id
            };
            // Only include departments if this is not a blueprint course
            if(!$scope.isBlueprint) {
                data.departments = [departmentId];
            }

            $http.post(url, data).then(
                function createCourseInstanceAfterCourse(response){
                    $scope.course.section = '001';
                    $scope.createCourseInstance(response.data.course_id);
                }, $scope.handleAjaxErrorWithMessage
            );

        };

        $scope.createCanvasCourse = function(){
            // format the department info to be passed into canvas as an account id
            var departmentId = 'dept:' + $scope.departments[
                    $scope.course.codeType.toLowerCase()];

            // Format the school ID, which will be used instead of the department ID if this is a blueprint course
            var schoolId = 'school:' + $scope.school.id;
            var url = djangoUrl.reverse(
                'canvas_site_creator:api_create_canvas_course');
            //get the template id
            var templateId = $scope.selectedTemplate;
            var data = {
                school_id: schoolId,
                dept_id: departmentId,
                course_instance_id: $scope.newCourseInstance.course_instance_id,
                course_code: $scope.course.code,
                section_id: $scope.newCourseInstance.section,
                term_id: $scope.newCourseInstance.term.meta_term_id,
                title: $scope.course.title,
                short_title: $scope.course.shortTitle,
                school: $scope.school.id,
                is_blueprint: $scope.isBlueprint
            };
            $http.post(url, data).then(
                function setCanvasCourse(response){
                    $scope.canvasCourse = response.data;
                    //Copy from template if selected
                    if (templateId !="No template" && templateId !='None'){
                        $scope.copyFromTemplate().then(
                            function updateTable(){
                                $scope.updateTablesWithCanvasCourseInfo();
                            });
                    }else{
                        $scope.updateTablesWithCanvasCourseInfo();
                    }
                },function handleError(response) {
                    $scope.handleAjaxErrorWithMessage(response,
                        "There was either a problem creating the Canvas site or " +
                        "creating the section for this course. ");
                }
            );

        };
        $scope.copyFromTemplate = function(){
            var url = djangoUrl.reverse(
                'canvas_site_creator:api_copy_from_canvas_template');
            var data = {
                template_id: $scope.selectedTemplate,
                canvas_course_id: $scope.canvasCourse.id,
            };
            return $http.post(url, data).then(
                function processTemplateCopy(response) {
                    $scope.templateUsed = true;
                }, function handleError(response) {
                    $scope.handleAjaxErrorWithMessage(response,
                        "There was a problem copying from the template " +
                        "for this course. ");
                }
            );
        };

        $scope.updateTablesWithCanvasCourseInfo = function(){
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                ['api/course/v2/course_instances/'
                + $scope.newCourseInstance.course_instance_id]);
            var data = {
                canvas_course_id: $scope.canvasCourse.id,
                sync_to_canvas: 1,
            };

            $http.patch(url, data).then(
                function postCourseSite(){
                    $scope.postCourseSiteAndMap();
                },function handleError(response) {
                    $scope.handleAjaxErrorWithMessage(response,
                        "There was a problem either updating the course " +
                        "instance table or setting the sync to Canvas flag. ");
                }
            );
        };

        $scope.postCourseSiteAndMap = function(){
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                ['api/course/v2/course_sites/']);
            var canvasCourseURL = window.globals.CANVAS_URL + '/courses/'
                + $scope.canvasCourse.id;
            var data = {
                external_id : canvasCourseURL,
                site_type_id : 'external'
            };

            $http.post(url, data).then(
                function updateCourseSite(response){
                    $scope.newCourseInstance.course_site_id =
                        response.data.course_site_id;
                    $scope.postSiteMap();
                },function handleError(response) {
                    $scope.handleAjaxErrorWithMessage(response,
                        "There was a problem updating the Course Site Table. ");
                }
            );
        };

        $scope.postSiteMap = function(){
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                ['api/course/v2/site_maps/']);
            var data = {
                course_instance : $scope.newCourseInstance.course_instance_id,
                course_site : $scope.newCourseInstance.course_site_id,
                map_type : 'official'
            };
            $http.post(url, data);
        };

        $scope.handleAjaxErrorResponse = function(response) {
            $log.error('Error attempting to ' + response.config.method + ' '
                + response.config.url + ': ' + response.status + ' ' +
                response.statusText + ': ' + JSON.stringify(response.data));
        };

        $scope.handleAjaxErrorWithMessage = function(response, customError) {
            var errorMsg = "A new course could not be created successfully. " +
                "Please try again.";
            if (customError) { errorMsg = customError + $scope.errorMessageSupport; }

            $scope.handleAjaxErrorResponse(response);
            $scope.failureModal = $uibModal.open({
                 controller: function($scope, errorMsg) {
                    $scope.errorMsg = errorMsg;
                },
                resolve: {
                    errorMsg: function() {
                        return errorMsg;
                    },
                },
                templateUrl: 'partials/create_new_course_failure_modal.html'
            });
            $scope.failureModal.result.finally(function clearFailureModal() {
                $scope.cancelCreateNewCourseInstance();
                $scope.failureModal = null;
            });
        };

        $scope.getCourseDisplayName = function() {
            if ($scope.newCourseInstance != null &&
                'course' in $scope.newCourseInstance) {
                return $scope.newCourseInstance.short_title ||
                    $scope.newCourseInstance.title;
            } else {
                return '';
            }
        };

        $scope.loadTermsAndDepartments = function() {
            // terms
            var termsUrl = djangoUrl.reverse('icommons_rest_api_proxy',
                                             ['api/course/v2/terms/'])
                           + '&school=' + $scope.school.id
                           + '&active=True&limit=1000' // TODO: api read-all-data
                           + '&with_end_date=True&with_start_date=True'
                           + '&ordering=-end_date,term_code__sort_order';
            $http.get(termsUrl).then(
                function successCallback(response) {
                    $scope.terms = response.data.results.map(function(term) {
                        return {id: term.term_id, name: term.display_name};
                    });
                    // now that we've loaded the terms, default to the most
                    // recent one.
                    if ($scope.terms.length > 0) {
                        $scope.course.term = $scope.terms[0].id;
                    }
                },
                $scope.handleAjaxErrorResponse
            );

            // departments
            var deptsUrl = djangoUrl.reverse('icommons_rest_api_proxy',
                                             ['api/course/v2/departments/'])
                           + '&school=' + $scope.school.id
                           + '&limit=1000'; // TODO: api read-all-data
            $http.get(deptsUrl).then(
                function successCallback(response) {
                    response.data.results.forEach(function(dept) {
                        if (dept.short_name == 'SB' ||
                                dept.short_name == 'ILE') {
                            $scope.departments[dept.short_name.toLowerCase()] =
                                dept.department_id;
                        }
                    });
                },
                $scope.handleAjaxErrorResponse
            );
        };
        $scope.loadTermsAndDepartments();
    } // end CreateNewCourseController()
})(); // end initCreateNewCourseController
