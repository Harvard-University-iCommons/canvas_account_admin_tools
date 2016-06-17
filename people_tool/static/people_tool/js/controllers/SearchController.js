(function() {
    var app = angular.module('PeopleTool');
    app.controller('SearchController', SearchController);

    function SearchController($scope, $compile, djangoUrl, $log, $timeout) {
        $scope.messages = [];
        $scope.operationInProgress = false;
        $scope.queryString = '';
        $scope.searchTypeOptions = [
            // `key` is the query key name to use with the $scope.queryString
            {key:'univ_id', name:'HUID or XID'},
            {key:'email_address', name:'Email Address'},
            {key:'search', name:'First OR Last Name'}
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
            // disable mouse events, including pointer style changes, for all
            // sorting headers and pagination buttons; assumes all columns are
            // sortable by default (otherwise need to store column state before
            // disabling sorting)
            $('#search-results-datatable th', 'a.paginate_button')
                .toggleClass('inert', !toggle);
            // todo: fix tab interactions
        };
        $scope.getProfileRoleTypeCd = function(profile) {
            return profile ? profile.role_type_cd : '';
        };
        $scope.renderId = function(data, type, full, meta) {
            return '<badge ng-cloak role="'
                + (full.role_type_cd ? full.role_type_cd : '')
                + '"></badge> ' + full.univ_id;
        };
        $scope.searchPeople = function(event) {
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
                infoEmpty: 'Showing 0 to 0 of 0 people',
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
                data: 'name_last',
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
