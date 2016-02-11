(function(){
    /**
     * Angular controller for the cross listing page.
     */
    var app = angular.module('CrossListCourses');
    app.controller('ListController',
        ['$scope', '$http', '$timeout', '$document', '$window', '$compile','djangoUrl',
        function($scope, $http, $timeout, $document, $window, $compile, $djangoUrl){

            $scope.dtInstance = null;

            $scope.formatCourse= function(course_instance) {
                return course_instance.course.school_id.toUpperCase()+
                                ' '+course_instance.course.registrar_code+
                                '-'+course_instance.term.display_name+
                                '-'+course_instance.course_instance_id;

            };

            $scope.dtOptions = {
                ajax: function(data, callback, settings) {
                    var url = $djangoUrl.reverse('icommons_rest_api_proxy',
                                                   ['api/course/v2/xlist_maps/']);

                    var queryParams = {
                        offset: data.start,
                        limit: data.length,
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
                createdRow: function( row, data, dataIndex ) {
                    // to use angular directives within the rendered datatable,
                    // we have to compile those elements ourselves.  joy.
                    $compile(angular.element(row).contents())($scope);
                },
                language: {
                    emptyTable: 'There are no cross listed courses  to display.',
                    info: 'Showing _START_ to _END_ of _TOTAL_ course mappings',
                    infoEmpty: 'Showing 0 to 0 of 0 course mappings',
                    paginate: {
                        next: '',
                        previous: '',
                    },
                },
                lengthMenu: [10, 25, 50, 100],
                // yes, this is a deprecated param.  yes, it's still required.
                // see https://datatables.net/forums/discussion/27287/using-an-ajax-custom-get-function-don-t-forget-to-set-sajaxdataprop
                sAjaxDataProp: 'data',
                searching: false,
                serverSide: true,
            };


            $scope.dtColumns = [
                {
                    data: null,
                    render: function(data, type, row) {

                        if (data.primary_course_instance ) {
                             return $scope.formatCourse(data.primary_course_instance);
                        } else {
                            return 'N/A';
                        }
                    },
                    title: 'Primary',
                },
                {
                    data: null,
                    render: function(data, type, full, meta) {

                        if (data.secondary_course_instance ) {
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
