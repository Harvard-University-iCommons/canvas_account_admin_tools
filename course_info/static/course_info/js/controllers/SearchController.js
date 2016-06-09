(function(){
    /**
     * Angular controller for the home page of course_info.
     */
    var app = angular.module('CourseInfo');
    
    app.controller('SearchController', ['$scope', '$http', '$timeout', '$document', '$window', 'djangoUrl', 'courseInstances',
        function($scope, $http, $timeout, $document, $window, djangoUrl, courseInstances){
            $scope.searchInProgress = false;
            $scope.queryString = '';
            $scope.showDataTable = false;
            $scope.columnFieldMap = {
                1: 'title',
                2: 'term__academic_year',
                3: 'term__display_name',
                5: 'course__registrar_code_display'
            };
            $scope.columnOrderable = {};
            $scope.filterOptions = {
                // `key` and `value` are the GET params sent to the server when
                // the option is chosen. `value` must be unique in its option list,
                // as it is also used for the HTML input element value. `value` can
                // be arbitrarily set to something unique if there are duplicate
                // values; in that case, an optional `query_value` attribute can be
                // included in the option object to indicate what to send to the
                // server. `query` is `true` if this option should trigger a GET
                // param included in the request, or `false` if it is e.g. the
                // default and should not be appended to the request params.
                sites: [
                    {key:'sites', value: 'all', name:'All courses', query: false, text: 'All courses <span class="caret"></span>'},
                    {key:'has_sites', value: 'True', name:'Only courses with sites', query: true, text: 'Only courses with sites <span class="caret"></span>'},
                    {key:'has_sites', value: 'False', name:'Only courses without sites', query: true, text: 'Only courses without sites <span class="caret"></span>'},
                    {key:'sync_to_canvas', value: 'sync_to_canvas_true', query_value: 'True', name:'Courses being synced to Canvas', query: true, text: 'Courses being synced to Canvas <span class="caret"></span>'}
                ],
                schools: [
                    // specific schools are filled out dynamically below
                ],
                terms: [
                    {key:'term_code', value: 'all', name:'All terms', query: false, text: 'All terms <span class="caret"></span>'}
                    // specific terms are filled out dynamically below
                ],
                years: [
                    {key:'academic_year', value: 'all', name:'All years', query: false, text: 'All years <span class="caret"></span>'}
                    // specific years are filled out dynamically below
                ]
            };

            $http.get('/icommons_rest_api/api/course/v2/term_codes/?limit=100')
                .then(function successCallback(response) {
                    $scope.filterOptions.terms =
                        $scope.filterOptions.terms.concat(response.data.results.map(function (tc) {
                            return {
                                key: 'term_code',
                                value: tc.term_code,
                                name: tc.term_name,
                                query: true,
                                text: tc.term_name + ' <span class="caret"></span>',
                            };
                        }));
                    if (response.data.next && response.data.next !== '') {
                        // API returns next=null if there are no more pages
                        console.log('Warning: Some terms missing from dropdown!');
                    }
                }, function errorCallback(response) {
                    console.log(response.statusText);
                });

            var year = (new Date()).getFullYear();
            var endYear = year + 1;
            var startYear = 2002;
            for (var i = endYear ; i >= startYear; i--) {
                $scope.filterOptions.years.push({
                    key: 'academic_year',
                    value: i + '',
                    name: i + '',
                    query: true,
                    text: i + ' <span class="caret"></span>'
                });
            }

            Array.prototype.push.apply(
                $scope.filterOptions.schools,
                $window.schoolOptions);

            $scope.filters = {
                // default to first in list on load
                schools: $scope.filterOptions.schools[0],
                sites: $scope.filterOptions.sites[0],
                terms: $scope.filterOptions.terms[0],
                // default to current year
                years: $scope.filterOptions.years[0]
            };

            $scope.enableColumnSorting = function(toggle) {
                var cols = $('#courseInfoDT').dataTable().fnSettings().aoColumns;
                $.each(cols, function(index, column){
                    if (toggle) {
                        // restore state
                        column.bSortable = $scope.columnOrderable[column.idx];
                    } else {
                        // save state before disabling
                        $scope.columnOrderable[column.idx] = column.bSortable;
                        column.bSortable = toggle;
                    }
                });
            };

            $scope.getCourseDescription = function(course) {
                // If a course's title is [NULL], attempt to display the short title.
                // If the short title is also [NULL], display [School] 'Untitled Course' [Term Display]
                console.log(course);
                if(typeof course.title != "undefined" && course.title.length > 0){
                    return course.title;
                }
                else if(typeof course.short_title != "undefined" && course.short_title.length > 0){
                    return course.short_title;
                }
                var school_id = course.course ? course.course.school_id.toUpperCase() : '';
                var term_display_name = course.term ? course.term.display_name : '';
                return school_id + ' Untitled Course ' + term_display_name;
            };

            $scope.courseInstanceToTable = function(course) {
                // This logic is reused in PeopelController.getFormattedCourseInstance
                // So any changes to data format need to be done in both places.
                // TODO: Eventually move the reusable logic to a separate library
                var cinfo = {};
                cinfo['description'] = $scope.getCourseDescription(course);
                cinfo['year'] = course.term ? course.term.academic_year : '';
                cinfo['term'] = course.term ? course.term.display_name : '';
                cinfo['term_code'] = course.term ? course.term.term_code : '';
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
                        || course.course.registrar_code).trim();
                    cinfo['school'] = course.course.school_id.toUpperCase();
                } else {
                    cinfo['code'] = '';
                    cinfo['school'] = '';
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

            var request = null;
            $scope.initializeDatatable = function() {
                $scope.dataTable = $('#courseInfoDT').DataTable({
                    deferLoading: 999, // number doesn't matter because table hidden
                    serverSide: true,
                    ajax: function(data, callback, settings) {
                        $timeout(function(){
                            $scope.searchInProgress = true;
                        }, 0);
                        $scope.enableColumnSorting(false);
                        //filter the sites flagged to be excluded(get only ones
                        // with exclude_from_isites set to 0)
                        var queryParameters = {
                            exclude_from_isites: 0};
                        if ($scope.queryString.trim() != '') {
                            queryParameters.search = $scope.queryString.trim();
                        }
                        for (var key in $scope.filters) {
                            var f = $scope.filters[key];
                            if (f.query) {
                                queryParameters[f.key] = f.query_value ? f.query_value : f.value;
                            }
                        }
                        queryParameters.offset = data.start;
                        queryParameters.limit = data.length;
                        var order = data.order[0];
                        queryParameters.ordering = (order.dir == 'desc' ? '-' : '') + $scope.columnFieldMap[order.column];
                        //if search request is already in progress, abort the previous one.
                        if (request) {
                            request.abort();
                            //restart the progress bar
                            $scope.searchInProgress = true;
                        }
                        request = $.ajax({
                            url: djangoUrl.reverse('icommons_rest_api_proxy',
                                                   ['api/course/v2/course_instances']),
                            method: 'GET',
                            data: queryParameters,
                            dataType: 'json',
                            success: function(data, textStatus, jqXHR) {
                                var results = data.results;
                                var resultsLength = data.results.length;
                                var processedData = results.map($scope.courseInstanceToTable);
                                // instances = { id: course_instance, ... }
                                courseInstances.instances = results.reduce(
                                    function(previousValue, currentValue, currentIndex, array) {
                                        previousValue[currentValue.course_instance_id] = currentValue;
                                        return previousValue;
                                    }, {});
                                callback({
                                    recordsTotal: data.count,
                                    recordsFiltered: data.count,
                                    data: processedData
                                });
                                $timeout(function() {
                                    $scope.dataTable.columns.adjust();
                                    $scope.showDataTable = true;
                                }, 0);
                            },
                            error: function(jqXHR, textStatus, errorThrown) {
                                console.log(textStatus);
                            },
                            complete: function() {
                                $scope.$apply(function(){
                                    $scope.searchInProgress = false;
                                });
                                $scope.enableColumnSorting(true);
                                //reset request when complete
                                request = null;
                            }
                        });
                    },
                    dom: '<<t>ip>',
                    language: {
                        info: 'Showing _START_ to _END_ of _TOTAL_ courses',
                        emptyTable: 'Your search didn&apos;t generate any results.' +
                        ' Please check your search criteria and try again.',
                        // datatables-bootstrap js adds glyphicons, so remove
                        // default Previous/Next text and don't add &laquo; or
                        // &raquo; as in that case the chevrons will be repeated
                        paginate: {
                            previous: '',
                            next: ''
                        }
                    },
                    order: [[1, 'asc']],  // order by course description
                    columns: [
                        {data: 'school'},
                        {
                            data: null,
                            render: function(data, type, row, meta) {
                                var url = '#/details/' + row.cid;
                                return '<a href="' + url + '">' + row.description + '</a>';
                            },
                        },
                        {data: 'year'},
                        {data: 'term'},
                        {
                            orderable: false,
                            render: function(data, type, row, meta) {
                                if (row.sites.length > 0) {
                                    var sites = row.sites.map(function(site) {
                                        return '<a href="' + site.course_site_url
                                                   + '" target="_blank">'
                                                   + site.site_id + '</a>';
                                    });
                                    return sites.join(', ');
                                } else {
                                    return 'N/A';
                                }
                            }
                        },
                        {data: 'code'},
                        {data: 'cid'},
                        {
                            orderable: false,
                            data: null,
                            render: function(data, type, full, meta) {
                                if (data.xlist_status != '') {
                                    return '<span class="label label-'
                                        + data.xlist_status_label + '">'
                                        + data.xlist_status + '</span>';
                                } else {
                                    return 'N/A';
                                }
                            }
                        }
                    ]
                });
            };

            $document.on('hidden.bs.dropdown', function(event) {
                var dropdown = $(event.target);
                dropdown.find('.dropdown-menu').attr('aria-expanded', false);
                dropdown.find('.dropdown-toggle').focus();
            });

            $scope.searchCourseInstances = function(event) {
                if (event.type == 'click' || (event.type == 'keypress' && event.which == 13)) {
                    // Call within timeout to prevent https://docs.angularjs.org/error/$rootScope/inprog?p0=$apply
                    $timeout(function () {
                        $scope.dataTable.ajax.reload();
                    }, 0);
                }
            }

            $scope.initializeDatatable();
        }]);
})();
