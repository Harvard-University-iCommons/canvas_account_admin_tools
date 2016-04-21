module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine-jquery', 'jasmine'],


    // list of files / patterns to load in the browser
    files: [
      'node_modules/angular/angular.js',
      'node_modules/angular-mocks/angular-mocks.js',
      'node_modules/angular-route/angular-route.js',
      'node_modules/angular-sanitize/angular-sanitize.js',
      'node_modules/jquery/dist/jquery.js',
      'node_modules/datatables.net/js/jquery.dataTables.js',
      'node_modules/datatables.net-bs/js/dataTables.bootstrap.js',
      'node_modules/angular-datatables/dist/angular-datatables.js',
      'node_modules/angular-ui-bootstrap/dist/ui-bootstrap-tpls.js',
      // need to ensure that the drf page-reader lib is called before the
      // service that depends on it is, so call out angular-drf.js explicitly.
      'course_info/tests/libraries/angular-drf.js',
      'course_info/**/*.js',
      'course_info/templates/course_info/partials/*.html',
    ],


    // list of files to exclude
    exclude: [
      // 'course_info/static/course_info/js/services/AngularDRFService.js',
    ],


    // preprocess matching files before serving them to the browser
    // available preprocessors: https://npmjs.org/browse/keyword/karma-preprocessor
    preprocessors: {
      'course_info/templates/course_info/partials/*.html': ['ng-html2js'],
    },


    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_DEBUG,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['PhantomJS'],


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,

    ngHtml2JsPreprocessor: {
      moduleName: 'templates',
      stripPrefix: 'course_info/templates/course_info/',
    },
  });
};
