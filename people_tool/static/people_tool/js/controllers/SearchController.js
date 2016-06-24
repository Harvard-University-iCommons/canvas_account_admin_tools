(function() {
    var app = angular.module('PeopleTool');
    app.controller('SearchController', SearchController);

    function SearchController($scope, $compile, djangoUrl, $log, $timeout) {
        // tracks state of interactive datatable elements
        $scope.datatableInteractiveElementTabIndexes = [];
        $scope.messages = [];
        $scope.operationInProgress = false;
        $scope.queryString = '';
        $scope.searchTypeOptions = [
            // `key` is the query key name to use with the $scope.queryString
            // `name` is the description to use for option labeling
            // `maxlength` is the max length allowed by the backend
            {key:'univ_id', name:'HUID or XID', maxLength:32},
            {key:'email_address', name:'Email Address', maxLength:284},
            {key:'search', name:'First OR Last Name', maxLength:30}
        ];
        $scope.searchType = $scope.searchTypeOptions[0];
        $scope.showDataTable = false;
        $scope.sortKeyByColumnId = {
            0: 'name_last',
            1: 'name_first',
            2: 'univ_id',
            3: 'email_address'
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
            var $inputs = $('#search-results-datatable_length select');

            // all clickable datatable elements
            var $links = $('#search-results-datatable th, a.paginate_button');

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

                // focus on search box; if user had tabbed to interactive
                // element and activated it by hitting enter, this prevents
                // it from being activated again by the keyboard while
                // operationInProgress
                $('#search-query-string').focus();
            }
        };
        $scope.getNameLast = function(name_last) {
            // If the short title is also [NULL], display [School] 'Untitled Course' [Term Display]
            if(typeof course.title != "undefined" && course.title.trim().length > 0){
                return course.title;
            }
            else if(typeof course.short_title != "undefined" && course.short_title.trim().length > 0){
                return course.short_title;
            }
            return 'Untitled Course';
        };
        $scope.getProfileRoleTypeCd = function(profile) {
            return profile ? profile.role_type_cd : '';
        };
        $scope.renderId = function(data, type, full, meta) {
            return '<badge ng-cloak role="'
                + (full.role_type_cd ? full.role_type_cd : '')
                + '"></badge> ' + full.univ_id;
        };
        $scope.renderPersonCoursesLink = function(data, type, full, meta) {
            // If person has no name, indicate this with some text so that we
            // can still display a clickable anchor link
            var lastName = (full.name_last.trim().length > 0) ?
                full.name_last : '(none)';
            return '<a href="' + '#/people/' + full.univ_id + '/courses/">'
                + lastName + '</a>';
        };
        $scope.searchPeople = function(event) {
            if ($scope.queryString.length > $scope.searchType.maxLength) {
                $scope.messages = [{
                    type: 'warning',
                    text: '"' + $scope.searchType.name + '" search term cannot '
                        + 'be greater than ' + $scope.searchType.maxLength
                        + ' characters in length.'
                }];
                return;
            }

            // Call within timeout to prevent
            // https://docs.angularjs.org/error/$rootScope/inprog?p0=$apply
            $timeout(function () {
                $scope.dtInstance.reloadData();
            }, 0);
        };
        $scope.queryStringInvalid = function() {
            return $scope.queryString.trim().length == 0;
        };
        $scope.updateSearchType = function(searchType) {
            // searchType is an element of the $scope.searchTypeOptions array
            $scope.searchType = searchType;
        };

        // configure the datatable
        $scope.dtInstance = null;
        $scope.dtOptions = {
            ajax: function(data, callback, settings) {
                $scope.toggleOperationInProgress(true);

                var url = djangoUrl.reverse('icommons_rest_api_proxy',
                                            ['api/course/v2/people/']);
                var queryParams = {
                    offset: data.start,
                    limit: data.length,
                    ordering: (data.order[0].dir === 'desc' ? '-' : '')
                              + $scope.sortKeyByColumnId[data.order[0].column]
                };
                queryParams[$scope.searchType.key] = $scope.queryString;

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
                        data: data.results
                    });
                })
                .fail(function dataTableGetFail(data, textStatus, errorThrown) {
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
            createdRow: function( row, data, dataIndex ) {
                // to use our 'badge' directive within the rendered datatable,
                // we have to compile those elements ourselves.
                $compile(angular.element(row).contents())($scope);
            },
            deferLoading: 0,
            language: {
                emptyTable: 'There are no people to display.',
                info: 'Showing _START_ to _END_ of _TOTAL_ people',
                infoEmpty: '',
                paginate: {
                    next: '',
                    previous: ''
                }
            },
            lengthMenu: [10, 25, 50, 100],
            // yes, this is a deprecated param.  yes, it's still required.
            // see https://datatables.net/forums/discussion/27287/using-an-ajax-custom-get-function-don-t-forget-to-set-sajaxdataprop
            sAjaxDataProp: 'data',
            searching: false,
            serverSide: true
        };

        $scope.dtColumns = [
            {
                render: $scope.renderPersonCoursesLink,
                title: 'Last Name'
            },
            {
                data: 'name_first',
                title: 'First Name'
            },
            {
                render: $scope.renderId,
                title: 'ID',
                width: '20%'
            },
            {
                data: 'email_address',
                title: 'Email'
            }
        ];

        // initialize
        $('#search-query-string').focus();
    }
})();
