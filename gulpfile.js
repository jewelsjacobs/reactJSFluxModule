'use strict';
/**
 * Gulp tasks.
 */
var browserify = require('browserify');
var del = require('del');
var gulp = require('gulp');
var reactify = require('reactify');
var streamify = require('gulp-streamify');
var source = require('vinyl-source-stream');
var uglify = require('gulp-uglify');
var browserSync = require('browser-sync');

// Settings
var SRC = './gui/src/';
var DEST = './gui/static/';

/**
 * Cleanup before running tasks.
 */
gulp.task('clean', function() {
    del([DEST + 'js/dist']);
    del([DEST + 'css/dist']);
});

/**
 * Bundle and minify our JS ... because we are legit.
 */
gulp.task('browserify', function() {
    var mainjs = SRC + 'js/main.js';
    browserify(mainjs)
        .transform(reactify)
        .bundle()
        .pipe(source('main.js'))
        // .pipe(streamify(uglify('main.js')))
        .pipe(gulp.dest(DEST + 'js/dist'));
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
gulp.task('watch', ['browser-sync'], function() {
    gulp.watch(
      'gui/static/js/!(dist)/**', ['default', browserSync.reload]
    );
});
