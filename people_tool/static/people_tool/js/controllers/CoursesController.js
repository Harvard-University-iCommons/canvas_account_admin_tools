(function() {
    var app = angular.module('PeopleTool');
    app.controller('CoursesController', CoursesController);

    function CoursesController($scope, $compile, djangoUrl, $log, $routeParams,
                               $timeout, personInfo) {
        // tracks state of interactive datatable elements
        $scope.datatableInteractiveElementTabIndexes = [];
        $scope.messages = [];
        $scope.operationInProgress = false;
        $scope.baseApiUrl = 'api/course/v2/';
        $scope.personId = $routeParams.personId;
        $scope.personCoursesUrl = $scope.baseApiUrl + 'people/'
            + $scope.personId + '/course_instances/';
        $scope.showCourseListDataTable = false;
        // maps course list datatable columns to API query params for ordering
        $scope.sortKeyByColumnId = {
            0: 'course__school_id',
            1: 'title',
            2: 'term__academic_year',
            3: 'term__display_name',
            5: 'course__registrar_code_display',
            6: 'course_instance_id'
        };
        $scope.courseInstanceDetailUrl = djangoUrl.reverse('course_info:index');

        $scope.setPersonDetails = function(personId){
            var url = djangoUrl.reverse(
                              'icommons_rest_api_proxy',
                              ['api/course/v2/people/']);
            var queryParams = {};
            queryParams['univ_id'] = personId;
            $.ajax({
                    url: url,
                    method: 'GET',
                    data: queryParams,
                    dataType: 'json'
            }).done(function dataTableGetDone(data, textStatus, jqXHR) {
                $scope.messages = [];
                var person = data.results[0];
                $scope.selectedPersonInfo = person;
            })
            .fail(function dataTableGetFail(data, textStatus, errorThrown) {
                $log.error('Error getting data from ' + url + ': '
                           + textStatus + ', ' + errorThrown);
            });
        };

        if  (angular.equals({}, personInfo.details)){
            //if the personInfo is not set (eg: when the page is loaded
            // from the course detail view), get the person detail from the backend
            $scope.setPersonDetails($scope.personId);
        }else{
            $scope.selectedPersonInfo = personInfo.details;
        }
        
        $scope.courseInstanceToTable = function(course) {
            // This logic is reused in the course_info app's PeopleController
            // and SearchController.
            // So any changes to data format need to be done in both places.
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
        $scope.getCourseDescription = function(course) {
            // If a course's title is [NULL], attempt to display the short title.
            // If the short title is also [NULL], display [School] 'Untitled Course' [Term Display]
            if(typeof course.title != "undefined" && course.title.trim().length > 0){
                return course.title;
            }
            else if(typeof course.short_title != "undefined" && course.short_title.trim().length > 0){
                return course.short_title;
            }
            return 'Untitled Course';
        };
        $scope.getProfileIdType = function(profile) {
            return profile ? profile.id_type : '';
        };
        $scope.toggleOperationInProgress = function(toggle) {
            $timeout(function() {
                // notify UI to start/stop showing in-progress messaging
                $scope.operationInProgress = toggle;
                // enable/disable interactive data table elements
                $scope.toggleDataTableInteraction(!toggle);
            }, 0);
        };
        $scope.toggleDataTableInteraction = function(toggle) {
            // enable/disable mouse and keyboard events, including pointer style
            // changes, for all page length and sorting headers and pagination
            // buttons; assumes all columns are sortable by default and that
            // page length is editable by default (otherwise need to store
            // element state before disabling)

            // all datatable input elements
            var $inputs = $('#person-courses-datatable_length select');

            // all clickable datatable elements
            var $links = $('#person-courses-datatable th, a.paginate_button');

            // update styling for links
            $links.toggleClass('inert', !toggle);

            if (toggle) {
                // restore tabindex state to enable keyboard interaction
                for (i=0; i < $links.length; i++) {
                    $links[i].setAttribute('tabindex',
                        $scope.datatableInteractiveElementTabIndexes[i]);
                }
                $scope.datatableInteractiveElementTabIndexes = [];
                $inputs.removeAttr('disabled');
            } else {
                // save tabindex state before disabling keyboard interaction
                for (i=0; i < $links.length; i++) {
                    $scope.datatableInteractiveElementTabIndexes.push(
                        $links[i].getAttribute('tabindex'));
                }

                // disable keyboard access
                $links.attr('tabindex', -1);
                $inputs.attr('disabled', '');

                // focus on breadcrumbs; if user had tabbed to interactive
                // element and activated it by hitting enter, this prevents
                // it from being activated again by the keyboard while
                // operationInProgress
                $('a').eq(0).focus();
            }
        };
        $scope.renderCourseDetailLink = function(data, type, full, meta) {
            return '<a href="'
                + window.globals.append_resource_link_id('../course_info/')
                + '#/details/' + full.cid + '?frompeoplecourses='
                + $scope.personId + '"><i class="fa fa-search"></i>'
                + '&nbsp;' + full.description + '</a>';
        };
        $scope.renderId = function(data, type, full, meta) {
            return '<badge ng-cloak role="' + full.id_type + '"></badge>' + full.univ_id;
        };
        $scope.renderSites = function(data, type, full, meta) {
            if (data.length > 0) {
                var sites = data.map(function (site) {
                    return '<a href="' + site.course_site_url
                        + '" target="_blank">' + site.site_id + '</a>';
                });
                return sites.join(', ');
            } else {
                return 'N/A';
            }
        };
        $scope.renderXlistMaps = function(data, type, full, meta) {
            if (full.xlist_status != '') {
                return '<span class="label label-' + full.xlist_status_label
                    + '">' + full.xlist_status + '</span>';
            } else {
                return 'N/A';
            }
        };

        // configure the course list datatable
        $scope.dtInstance = null;
        $scope.dtOptions = {
            ajax: function(data, callback, settings) {
                $scope.toggleOperationInProgress(true);

                var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                            [$scope.personCoursesUrl]);
                var queryParams = {
                    limit: data.length,
                    offset: data.start,
                    ordering: (data.order[0].dir === 'desc' ? '-' : '')
                              + $scope.sortKeyByColumnId[data.order[0].column]
                };

                $.ajax({
                    url: url,
                    method: 'GET',
                    data: queryParams,
                    dataSrc: 'data',
                    dataType: 'json'
                }).done(function dataTableGetDone(data, textStatus, jqXHR) {
                    $scope.messages = [];
                    callback({
                        recordsTotal: data.count,
                        recordsFiltered: data.count,
                        data: data.results.map($scope.courseInstanceToTable)
                    });
                    $timeout(function() {
                        $scope.dtInstance.DataTable.columns.adjust();
                        $scope.showCourseListDataTable = true;
                    }, 0);
                })
                .fail(function dataTableGetFail(data, textStatus, errorThrown) {
                    // todo: update these messages
                    $log.error('Error getting data from ' + url + ': '
                               + textStatus + ', ' + errorThrown);
                    // no need for multiple messages at the moment, just
                    // override any existing message
                    $scope.messages = [{
                        type: 'danger',
                        text: 'Server error. Search cannot be completed at ' +
                              'this time. '
                    }];
                    callback({
                        recordsTotal: 0,
                        recordsFiltered: 0,
                        data: []
                    });
                })
                .always(function dataTableGetAlways() {
                    $scope.toggleOperationInProgress(false);
                    $scope.$digest();
                });
            },
            language: {
                emptyTable: 'There are no courses to display.',
                info: 'Showing _START_ to _END_ of _TOTAL_ courses',
                infoEmpty: '',
                // datatables-bootstrap js adds glyphicons, so remove
                // default Previous/Next text and don't add &laquo; or
                // &raquo; as in that case the chevrons will be repeated
                paginate: {
                    next: '',
                    previous: ''
                }
            },
            lengthMenu: [10, 25, 50, 100],
            order: [[1, 'asc']],  // order by course description
            // yes, this is a deprecated param.  yes, it's still required.
            // see https://datatables.net/forums/discussion/27287/using-an-ajax-custom-get-function-don-t-forget-to-set-sajaxdataprop
            sAjaxDataProp: 'data',
            searching: false,
            serverSide: true
        };

        $scope.dtColumns = [
            {
                data: 'school',
                title: 'School'
            },
            {
                render: $scope.renderCourseDetailLink,
                title: 'Course Details'
            },
            {
                data: 'year',
                title: 'Academic Year'
            },
            {
                data: 'term',
                title: 'Academic Term'
            },
            {
                data: 'sites',
                orderable: false,
                render: $scope.renderSites,
                title: 'Associated Site'
            },
            {
                data: 'code',
                title: 'Course Code'
            },
            {
                data: 'cid',
                title: 'SIS/Course Instance ID'
            },
            {
                orderable: false,
                render: $scope.renderXlistMaps,
                title: 'Cross Listing'
            }
        ];
    }
})();
