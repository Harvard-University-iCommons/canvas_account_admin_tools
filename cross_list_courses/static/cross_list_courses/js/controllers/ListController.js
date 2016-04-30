(function(){
    /**
     * Angular controller for the cross listing page.
     */
    var app = angular.module('CrossListCourses');
    app.controller('ListController', ListController);

    function ListController($scope, $http, $timeout, $document, $window,
                            $compile, djangoUrl, $log, $q) {
        $scope.message = null;
        $scope.operationInProgress = false;
        $scope.rawFormInput = {primary: '', secondary: ''};

        $scope.cleanCourseInstanceInput = function (courseInstanceString) {
            return courseInstanceString.trim();
        };
        $scope.clearMessages = function () {
            $scope.message = null;
        };
        $scope.formatCourse = function (course_instance) {
            return course_instance.course.school_id.toUpperCase() +
                ' ' + course_instance.course.registrar_code +
                '-' + course_instance.term.display_name +
                '-' + course_instance.course_instance_id;
        };
        $scope.handleAjaxError = function (data, status, headers, config, statusText) {
            $log.error('Error attempting to ' + config.method + ' ' + config.url +
                ': ' + status + ' ' + statusText + ': ' + JSON.stringify(data));
        };
        $scope.handleAjaxErrorResponse = function (r) {
            // angular promise then() function returns a response object,
            // unpack for our old-style error handler
            $scope.handleAjaxError(
                r.data, r.status, r.headers, r.config, r.statusText);
        };
        $scope.invalidInput = function () {
            return (!$scope.isValidCourseInstance($scope.rawFormInput.primary) || !$scope.isValidCourseInstance($scope.rawFormInput.secondary))
                || ($scope.cleanCourseInstanceInput($scope.rawFormInput.primary) ==
                $scope.cleanCourseInstanceInput($scope.rawFormInput.secondary))
        };
        $scope.isValidCourseInstance = function (courseInstanceString) {
            return $scope.cleanCourseInstanceInput(courseInstanceString)
                .match(/^[0-9]+$/);
        };
        $scope.postNewCrosslisting = function (primary, secondary) {
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                ['api/course/v2/xlist_maps/']);

            // todo: this is the call to make, switch when backend is ready
            // return $http.post(url,
            //     {primary: primary, secondary: secondary});

            // temporarily return a random success, failure, or backend msg
            var deferred = $q.defer();
            $timeout(function () {
                return Math.round(Math.random())
                    ? deferred.resolve({})
                    : Math.round(Math.random())
                    ? deferred.reject({error: {detail: 'specific error detail from the backend'}})
                    : deferred.reject({});
            }, 1000);
            return deferred.promise;
        };
        $scope.submitAddCrosslisting = function () {
            $scope.clearMessages();
            $scope.operationInProgress = true;

            var primary = $scope.cleanCourseInstanceInput(
                $scope.rawFormInput.primary);
            var secondary = $scope.cleanCourseInstanceInput(
                $scope.rawFormInput.secondary);

            $scope.postNewCrosslisting(primary, secondary)
                .then(function postSucceeded(response) {
                    $scope.message = {
                        alertType: 'success',
                        text: primary + ' was successfully crosslisted with ' +
                        secondary + '.'
                    };
                    $scope.dtInstance.reloadData();
                }, function postFailed(response) {
                    // todo: enable once hooked up to backend
                    // $scope.handleAjaxErrorResponse(response);
                    var errorText = '';
                    if (((response || {}).error || {}).detail) {
                        errorText = response.error.detail;
                    } else {
                        errorText = primary + ' could not be ' +
                            'crosslisted with ' + secondary + ' at this ' +
                            'time. Please check the course instance IDs ' +
                            'and try again.';
                    }
                    $scope.message = {alertType: 'danger', text: errorText};
                }).finally(function cleanupAfterPost() {
                $scope.operationInProgress = false;
            });
        };

        /**
         * Datatable setup and helpers
         */

        $scope.dtInstance = null;

        function renderCourseInstance(courseInstance) {
            if (courseInstance) {
                return $scope.formatCourse(courseInstance);
            } else {
                return 'N/A';
            }
        }

        $scope.dtOptions = {
            ajax: function (data, callback, settings) {
                var url = djangoUrl.reverse('icommons_rest_api_proxy',
                    ['api/course/v2/xlist_maps/']);

                var queryParams = {
                    offset: data.start,
                    limit: data.length,
                    ordering: '-primary_course_instance__term__calendar_year,primary_course_instance__term__school_id',
                    include: 'course_instance',
                };

                $.ajax({
                    url: url,
                    method: 'GET',
                    data: queryParams,
                    dataSrc: 'data',
                    dataType: 'json',
                    success: function (data, textStatus, jqXHR) {
                        callback({
                            recordsTotal: data.count,
                            recordsFiltered: data.count,
                            data: data.results,
                        });
                    },
                    error: function (data, textStatus, errorThrown) {
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
                processing: '<i class="fa fa-refresh fa-spin"></i> Loading...',
            },
            lengthMenu: [10, 25, 50, 100],
            // yes, this is a deprecated param.  yes, it's still required.
            // see https://datatables.net/forums/discussion/27287/using-an-ajax-custom-get-function-don-t-forget-to-set-sajaxdataprop
            sAjaxDataProp: 'data',
            searching: false,
            serverSide: true,
            processing: true,
            ordering: false,
        };

        $scope.dtColumns = [
            {
                data: null,
                render: function (data) {
                    return renderCourseInstance(
                        data.primary_course_instance);
                },
                title: 'Primary',
                bSortable: false,
            },
            {
                data: null,
                render: function (data) {
                    return renderCourseInstance(
                        data.secondary_course_instance);
                },
                title: 'Secondary',
            },
        ];

    }
})();
