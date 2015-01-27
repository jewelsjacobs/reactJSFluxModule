'use strict';
/**
 * Gulp tasks.
 */
var browserify = require('browserify');
var del = require('del');
var gulp = require('gulp');
var reactify = require('reactify');
var envify = require('envify/custom');
var streamify = require('gulp-streamify');
var source = require('vinyl-source-stream');
var uglify = require('gulp-uglify');
var gutil = require('gulp-util');
var glob = require("glob");
var gulpif = require('gulp-if');
var requireglobify = require('require-globify');

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
      .transform(envify({
        NODE_ENV: gutil.env.type
      }))
      .transform(requireglobify)
      .bundle()
      .pipe(source(filename))
      .pipe(gulpif(gutil.env.type === 'production', streamify(uglify(filename))))
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
