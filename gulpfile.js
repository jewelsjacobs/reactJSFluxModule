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
var browserSync = require('browser-sync');

/**
 * Cleanup before running tasks.
 */
gulp.task('clean', function() {
  del(['gui/static/js/dist']);
  del(['gui/static/css/dist']);
});

// Browserify task.
gulp.task('browserify', function() {
  var mainjs = __dirname + '/gui/src/js/main.js';
  browserify(mainjs)
    .transform(reactify)
    .transform(envify)
    .bundle()
    .pipe(source('main.js'))
    //.pipe(streamify(uglify('main.js')))
    .pipe(gulp.dest('gui/static/dist/js'));
});

/**
 * Browser-sync task for starting the server.
 */
gulp.task('browser-sync', function() {
  browserSync({
    proxy: "localhost:5051"
  });
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
  gulp.watch('app/**', ['default']);
});

gulp.task('watch', function() {
    gulp.watch(
      'gui/src/js/**', ['default']
    );
});
