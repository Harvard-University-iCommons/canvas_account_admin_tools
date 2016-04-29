(function(){
    /**
     * Angular controller for the cross listing page.
     */
    var app = angular.module('CrossListCourses');
    app.controller('ListController',
        ['$scope', '$http', '$timeout', '$document', '$window', '$compile','djangoUrl','$log',
        function($scope, $http, $timeout, $document, $window, $compile, $djangoUrl, $log){

            $scope.dtInstance = null;
            $scope.message = null;
            $scope.operationInProgress = false;
            // todo: strip()
            $scope.primaryCourseInput = '';
            $scope.secondaryCourseInput = '';

            $scope.formatCourse = function(course_instance) {
                return course_instance.course.school_id.toUpperCase() +
                                ' ' + course_instance.course.registrar_code +
                                '-' + course_instance.term.display_name +
                                '-' + course_instance.course_instance_id;
            };

            $scope.invalidInput = function() {
                return !$scope.isValidCourseInstance($scope.primaryCourseInput) ||
                        !$scope.isValidCourseInstance($scope.secondaryCourseInput)
            };

            $scope.isValidCourseInstance = function(courseInstanceString) {
                return courseInstanceString.match(/[0-9]+/);
            };

            $scope.submitAddCrosslisting = function() {
                $scope.clearMessages();
                $scope.operationInProgress = true;
                // todo: make the call, process it
                $timeout(function() {
                    $scope.message = {
                        alertType: 'success',
                        text: $scope.primaryCourseInput + ' was successfully crosslisted with ' + $scope.secondaryCourseInput + '.'
                    };
                    $scope.operationInProgress = false;
                }, 1000);
                // todo: reload datatable
            };

            $scope.clearMessages = function() {
                $scope.message = null;
            };

            $scope.dtOptions = {
                ajax: function(data, callback, settings) {
                    var url = $djangoUrl.reverse('icommons_rest_api_proxy',
                                                   ['api/course/v2/xlist_maps/']);

                    var queryParams = {
                        offset: data.start,
                        limit: data.length,
                        ordering:'-primary_course_instance__term__calendar_year,primary_course_instance__term__school_id',
                        include: 'course_instance',
                    };

                    $.ajax({
                        url: url,
                        method: 'GET',
                        data: queryParams,
                        dataSrc: 'data',
                        dataType: 'json',
                        success: function(data, textStatus, jqXHR) {
                            callback({
                                recordsTotal: data.count,
                                recordsFiltered: data.count,
                                data: data.results,
                            });
                        },
                        error: function(data, textStatus, errorThrown) {
                            $log.error('Error getting data from ' + url + ': '
                                       + textStatus + ', ' + errorThrown);
                            callback({
                                recordsTotal: 0,
                                recordsFiltered: 0,
                                data: [],
                            });
                        },
                    });
                },
                language: {
                    emptyTable: 'There are no cross listed courses to display.',
                    info: 'Showing _START_ to _END_ of _TOTAL_ course mappings',
                    infoEmpty: 'Showing 0 to 0 of 0 course mappings',
                    paginate: {
                        next: '',
                        previous: '',
                    },
                    processing: '<img src="' + window.globals.STATIC_URL + 'images/ajax-loader-large.gif" class="loading"/> Loading...',
                },
                lengthMenu: [10, 25, 50, 100],
                // yes, this is a deprecated param.  yes, it's still required.
                // see https://datatables.net/forums/discussion/27287/using-an-ajax-custom-get-function-don-t-forget-to-set-sajaxdataprop
                sAjaxDataProp: 'data',
                searching: false,
                serverSide: true,
                processing:true,
                ordering: false,
            };

            $scope.dtColumns = [
                {
                    data: null,
                    render: function(data, type, row) {
                        if (data.primary_course_instance) {
                             return $scope.formatCourse(data.primary_course_instance);
                        } else {
                            return 'N/A';
                        }
                    },
                    title: 'Primary',
                    bSortable: false,
                },
                {
                    data: null,
                    render: function(data, type, full, meta) {
                        //TODO: explore refactoring the render code that is
                        // duplicated for both columns
                        if (data.secondary_course_instance) {
                            return $scope.formatCourse(data.secondary_course_instance);

                        } else {
                            return 'N/A';
                        }
                    },
                    title: 'Secondary',
                },
            ];

        }]);
})();
