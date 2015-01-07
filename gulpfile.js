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

/**
 * Cleanup before running tasks.
 */
gulp.task('clean', function() {
    del(['gui/static/js/dist']);
    del(['gui/static/css/dist']);
});

/**
 * Bundle and minify our JS ... because we are legit.
 */
gulp.task('browserify', function() {
    var mainjs = __dirname + '/gui/static/js/main.js';
    browserify(mainjs)
        .transform(reactify)
        .bundle()
        .pipe(source('main.js'))
        // .pipe(streamify(uglify('main.js')))
        .pipe(gulp.dest('gui/static/js/dist'));
});

/**
 * Default task which run our other pertinent tasks.
 */
gulp.task('default', ['clean', 'browserify']);

/**
 * A watcher task to automatically build as you work.
 */
gulp.task('watch', function() {
    gulp.watch('gui/static/js/!(dist)/**', ['default']);
});
