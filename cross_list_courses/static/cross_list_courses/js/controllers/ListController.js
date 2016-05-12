(function(){
    /**
     * Angular controller for the cross listing page.
     */
    var app = angular.module('CrossListCourses');
    app.controller('ListController', ListController);

    function ListController($scope, $http, $timeout, $document, $window,
                            $compile, djangoUrl, $log, $q, $uibModal) {
        // expected $scope.message format:
        //   {alertType: 'bootstrap alert class', text: 'actual message'}
        $scope.message = null;
        // operationInProgress can be 'add' or 'remove' -- the distinction is
        // made so that the submit button for the add doesn't show a spinning
        // progress icon while the modal is processing a remove request
        $scope.operationInProgress = null;
        $scope.rawFormInput = {primary: '', secondary: ''};

        $scope.cleanCourseInstanceInput = function (courseInstanceString) {
            return courseInstanceString.trim();
        };
        $scope.clearMessages = function () {
            $scope.message = null;
        };
        $scope.confirmRemove = function(xlistMap) {
            var primaryId = xlistMap.primary_course_instance.course_instance_id;
            var secondaryId = xlistMap.secondary_course_instance.course_instance_id;
            $scope.confirmRemoveModalInstance = $uibModal.open({
                controller: function($scope, primary, secondary) {
                    $scope.primary = primary;
                    $scope.secondary = secondary;
                    $scope.clearMessages();
                    $scope.confirm = function() {
                        $scope.removeCrosslisting(xlistMap.xlist_map_id,
                            primaryId, secondaryId)
                        .finally(function closeModal(){
                            $scope.$close();  // close modal
                            $scope.confirmRemoveModalInstance = null;
                        });
                    }
                },
                resolve: {
                    primary: function() {
                        return primaryId;
                    },
                    secondary: function() {
                        return secondaryId;
                    }
                },
                // can access parent scope so it can call removeCrosslisting()
                scope: $scope,
                templateUrl: 'partials/remove-xlist-map-confirmation.html',
            });
        };
        $scope.deleteCrosslisting = function (xlistMapId) {
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                ['api/course/v2/xlist_maps/' + xlistMapId + '/']);
            return $http.delete(url);
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
            // convert the result of regex match() to boolean
            return !!($scope.cleanCourseInstanceInput(courseInstanceString)
                .match(/^[0-9]+$/));
        };
        $scope.postNewCrosslisting = function (primary, secondary) {
            var url = djangoUrl.reverse('icommons_rest_api_proxy',
                ['api/course/v2/xlist_maps/']);

            return $http.post(url, {
                primary_course_instance: primary,
                secondary_course_instance: secondary
            });
        };
        $scope.removeCrosslisting = function(xlistMapId, primary, secondary) {
            $scope.operationInProgress = 'remove';

            var promise = $scope.deleteCrosslisting(xlistMapId)
                .then(function deleteSucceeded(response) {
                    $scope.message = {
                        alertType: 'success',
                        text: 'Successfully de-cross-listed ' + primary +
                            ' and  ' + secondary + '.'
                    };
                }, function DeleteFailed(response) {
                    $scope.handleAjaxErrorResponse(response);
                    errorText = 'Could not de-cross-list ' + primary +
                        ' and ' + secondary + '. Please try again later.';
                    $scope.message = {alertType: 'danger', text: errorText};
                }).finally(function cleanupAfterDelete() {
                    // always reload, in case the failure was a 404
                    $scope.dtInstance.reloadData();
                    $scope.operationInProgress = null;
                });

            return promise;
        };
        $scope.submitAddCrosslisting = function () {
            $scope.clearMessages();
            $scope.operationInProgress = 'add';

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
                    $scope.handleAjaxErrorResponse(response);
                    var errorText = '';
                    var nonFieldErrors = ((response || {}).data || {}).non_field_errors;
                    if ((response || {}).status == 400 && angular.isArray(nonFieldErrors)) {
                        // transform backend errors to user-friendly versions
                        var errorsForUI = nonFieldErrors.map(function(errorDetail) {
                            if (errorDetail.indexOf('unique set') > -1) {
                                return primary + ' is already crosslisted ' +
                                    'with ' + secondary + '.';
                            } else {
                                return errorDetail;
                            }
                        });
                        // backend returns array of errors; use only the first
                        errorText = errorsForUI[0];
                    } else {
                        errorText = primary + ' could not be ' +
                            'crosslisted with ' + secondary + ' at this ' +
                            'time. Please check the course instance IDs ' +
                            'and try again.';
                    }
                    $scope.message = {alertType: 'danger', text: errorText};
                }).finally(function cleanupAfterPost() {
                    $scope.operationInProgress = null;
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
        function renderRemove(data, type, full, meta) {
            var icon = '<i class="fa fa-trash-o"></i>';
            var link = '<a href="" data-toggle="tooltip" ' +
                'data-placement="left" title="De-cross-list courses"' +
                'ng-click="confirmRemove(dtInstance.DataTable.data()[' +
                meta.row + '])" ' + 'data-xlist-map-id="' +
                full.xlist_map_id + '">' + icon + '</a>';
            return '<div class="text-center">' + link + '</div>';
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
            createdRow: function( row, data, dataIndex ) {
                // to use angular directives within the rendered datatable,
                // we have to compile those elements ourselves.  joy.
                $compile(angular.element(row).contents())($scope);
            },
            drawCallback: function() {
                $('[data-toggle="tooltip"]').tooltip();
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
            {
                data: null,
                orderable: false,
                render: renderRemove,
                width: '10%'
            },
        ];

    }
})();
