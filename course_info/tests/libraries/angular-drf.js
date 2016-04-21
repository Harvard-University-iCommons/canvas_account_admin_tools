/**
 angular-def v1.0.0

 The angularDRF service provides a single get(url, config) method that will
 pull in all pages of a django rest framework's response for you, returned as
 a promise.  The config object should look like an $http configuration object,
 with the following additional keys:

 config = {
     ...
     drf: {
         pageSize: 50,                  // defaults to 100
         numParallelRequests: 3,        // defaults to 5
     },
 }

 NOTE: this library assumes the server is using limit/offset paging.
 NOTE: this library will overwrite `config.params.limit` and
       `config.params.offset` as needed
 TODO: take the paging strategy as a parameter.

 The value passed into the promise's reject handler will be an Error object.
 If triggered by an http failure, the error message will include a json
 serialization of the error response.


 Usage:
 // register the service to the app
 var app = angular.module('myModule', ...);
 app.factory('angularDRF', ['$http', '$q', angularDRF]);

 // then from within a scope or controller method
 var config = {
     'url': 'https://server/path',
     'drf': {'numParallelRequests': 5},
 };
 angularDRF.get(url, config).then(
     function(entities) {
         // entities contains the full set of data
     },
     function(errorResponse) {
        // errorResponse is the first http error response we saw
     },
 );

 **/

function angularDRF($http, $q) {
    function makeRequests(url, config, pageParamsList) {
        // makes an http request for each page param in the given list,
        // and returns a promise that resolves once all the http requests
        // return, containing an array of those http responses.
        promises = pageParamsList.map(function(params) {
            var pageConfig = angular.merge({}, config, {'params': params});
            return $http.get(url, pageConfig);
        });
        return $q.all(promises);
    }

    // TODO: should this be an $http transformResponse method?
    function rejectIfNotJson(reject, response) {
        // since we expect json, treat non-object responses as errors
        if (!angular.isObject(response.data)) {
            rejectWithError(reject, response);
        }
    }

    function rejectWithError(reject, error) {
        // transform http error response to Error as needed
        if (!(error instanceof Error)) {
            // try to pretty-print it if it looks like an http response
            if (angular.isObject(error) &&
                    error.hasOwnProperty('status') &&
                    error.hasOwnProperty('statusText') &&
                    error.hasOwnProperty('config') &&
                    error.hasOwnProperty('data')) {
                error = new Error(
                            error.config.method + ' ' + error.config.url +
                            ' returned ' + error.status + ' ' +
                            error.statusText + ': ' +
                            JSON.stringify(error));
            }
            // otherwise, just try to stringify it
            else {
                error = new Error(JSON.stringify(error));
            }
        }
        reject(error);
    }

    // drf is the service we're returning from this factory
    var drf = {}
    drf.get = function(url, config) {
        var pageSize = 100;
        var numParallelRequests = 5;
        if (angular.isUndefined(config)) {
            config = {};
        }
        if (angular.isObject(config.drf)) {
            pageSize = config.drf.pageSize || 100;
            numParallelRequests = config.drf.numParallelRequests || 5;
        }

        // drf.get() returns a promise that will either resolve with the full
        // set of data requested, or will reject with an http error response.
        return $q(function(resolve, reject) {
            // request the initial page
            var pageConfig = angular.merge({}, config,
                                           {'params': {'offset': 0,
                                                       'limit': pageSize}});
            $http.get(url, pageConfig).then(
                function firstPageSuccess(response) {
                    // if we didn't get a json response, error out
                    rejectIfNotJson(reject, response);

                    // copy out the data from the first response.  later
                    // responses will have their data appended to this list.
                    var entities = angular.copy(response.data.results);

                    // generate our list of query params, now that we know the
                    // total count.
                    var pageParamsList = [];
                    for (var offset=pageSize;
                            offset < response.data.count;
                            offset += pageSize) {
                        pageParamsList.push({'offset': offset, 'limit': pageSize});
                    }

                    // slice them up into "make N parallel requests at once"
                    // chunks now to avoid closure-inside-a-for-loop issues
                    // in the setting-up-promise-chain step.
                    var chunks = [];
                    for (var i=0; i<pageParamsList.length; i+=numParallelRequests) {
                        chunks.push(
                            pageParamsList.slice(i, i+numParallelRequests));
                    }

                    // set up a promise chain where we make N http requests
                    // in parallel, handle their results, then make another
                    // N calls, etc.  see
                    //     http://www.html5rocks.com/en/tutorials/es6/promises/#toc-parallelism-sequencing
                    // for the example this was based on, and a good primer on
                    // promises.
                    var sequence = $q.resolve();
                    chunks.forEach(function(chunk) {
                        sequence = sequence.then(function() {
                            return makeRequests(url, config, chunk);
                        }).then(function(chunkResponses) {
                            chunkResponses.forEach(function(response) {
                                rejectIfNotJson(reject, response);
                                Array.prototype.push.apply(
                                    entities, response.data.results);
                            });
                        });
                    });

                    // if any of the calls along the way error out, either due
                    // to http errors or json issues, we catch it here, before
                    // the resolve happens.
                    sequence = sequence.catch(function(err) {
                        rejectWithError(reject, err);
                    });

                    // once the sequence is complete, we have all the data,
                    // and we can resolve the promise that drf.get() returned.
                    sequence = sequence.then(function() {
                        resolve(entities);
                    });
                    
                    return sequence;
                },
                function firstPageFailure(response) {
                    rejectWithError(reject, response);
                }
            );
        });
    };
    return drf;
}
