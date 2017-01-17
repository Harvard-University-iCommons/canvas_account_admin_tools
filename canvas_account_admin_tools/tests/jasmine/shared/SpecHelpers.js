var spec = {};

spec.diSanityCheck = function(providerList) {
  providerList.forEach(function (thing) {
    expect(thing).not.toBeUndefined();
    expect(thing).not.toBeNull();
  });
};

spec.getParamsAndRespondWith = function(options) {
  var o = options || {};
  var method = o.method || 'GET';
  var response = o.response || {};
  var url = o.url || /.*/;
  var statusCode = o.statusCode || 200;

  var actualParams = null;

  this.$httpBackend.expect(method, url, o.content).respond(
    function captureParamsAndReturnDesiredResponse(m, u, d, h, params) {
      actualParams = params;
      return [statusCode, response];
    });

  if (!o.flushLater) { this.$httpBackend.flush(1); }

  return actualParams;
};

spec.verifyNoOutstanding = function() {
  // sanity checks to make sure no http calls are still pending
  this.$httpBackend.verifyNoOutstandingExpectation();
  this.$httpBackend.verifyNoOutstandingRequest();
};
