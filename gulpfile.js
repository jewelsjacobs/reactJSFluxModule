'use strict';
/**
 * Gulp tasks.
 */
var browserify = require('browserify');
var del = require('del');
var gulp = require('gulp');
var reactify = require('reactify');
var envify = require('envify');
var streamify = require('gulp-streamify');
var source = require('vinyl-source-stream');
var uglify = require('gulp-uglify');
var gutil = require('gulp-util');
var glob = require("glob");
var gulpif = require('gulp-if');

// Set some defaults
var isDev  = true;
var isProd = false;

// This allows 'gulp --type production' in the cli to build a browserfied, uglified version of main.js
// while anything else will maintain a non uglified main.js file for easier debugging.
if(gutil.env.type === 'production') {
  isDev  = false;
  isProd = true;
}

/**
 * Cleanup before running tasks.
 */
gulp.task('clean', function() {
  del(['gui/static/dist/js']);
  del(['gui/static/dist/css']);
});

// Browserify task. Supports multiple modules
gulp.task('browserify', function() {
  glob(__dirname + "/gui/src/js/*/*.js", function (er, files) {
    var file = files[0];
    var filename = file.split("/").pop();
    browserify(file)
      .transform(reactify)
      .transform(envify)
      .bundle()
      .pipe(source(filename))
      .pipe(gulpif(isProd, streamify(uglify(filename))))
      .pipe(gulp.dest('gui/static/dist/js'));
  })
});

/**
 * Default task which run our other pertinent tasks.
 */
gulp.task('default', ['clean', 'browserify']);

/**
 * A watcher task to automatically build as you work.
 */
// Define the watch task.
gulp.task('watch', function() {
    gulp.watch(
      'gui/src/js/**', ['default']
    );
});
