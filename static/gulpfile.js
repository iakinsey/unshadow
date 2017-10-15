'use strict';


var browserify  = require('browserify'),
    gulp        = require('gulp'),
    gulpif      = require('gulp-if'),
    streamify   = require('gulp-streamify'),
    source      = require('vinyl-source-stream'),
    buffer      = require('vinyl-buffer'),
    uglify      = require('gulp-uglify'),
    sourcemaps  = require('gulp-sourcemaps'),
    path        = require('path'),
    fileinclude = require('gulp-file-include'),
    pkg         = require('./package.json'),
    replace     = require('gulp-replace'),
    concatCss   = require('gulp-concat-css');


var getBundleName = function () {
    return pkg.name + '-' + pkg.version;
};


var folder = function (dir) {
    return path.join(__dirname, dir);
};


///////////////////////////////////////////////////////////////////////////////
// Settings
///////////////////////////////////////////////////////////////////////////////

var options = {
    debug: false
};

var dist = {
    js          : folder('dist/js/'),
    js_file     : getBundleName() + '.js',
    css_file    : getBundleName() + '.css',
    css         : folder('dist/css/'),
    html        : folder('dist/'),
    root        : folder('dist/')
};


var src = {
    html_index  : folder('html/index.html'),
    js_main     : folder('js/main.js'),
    html        : folder('html/**/*.html'),
    js_dir      : folder('js/'),
    js          : folder('js/**/*.js*'),
    css         : folder('css/**/*.css'),
    assets      : folder('assets/**')
};


///////////////////////////////////////////////////////////////////////////////
// JS Task
///////////////////////////////////////////////////////////////////////////////


gulp.task('js', function() {
    return browserify({debug: options.debug})
        .add(src.js_main)
        .bundle()
        .pipe(source(getBundleName() + '.js'))
        .pipe(buffer())
        //.pipe(gulpif(!options.debug, streamify(uglify())))
        .pipe(gulpif(options.debug, sourcemaps.init({loadMaps: true})))
        .pipe(gulpif(options.debug, sourcemaps.write('./')))
        .pipe(gulp.dest(dist.js));
});


///////////////////////////////////////////////////////////////////////////////
// HTML Task
///////////////////////////////////////////////////////////////////////////////


gulp.task('html', function () {
    gulp.src([src.html_index])
        .pipe(fileinclude({
            prefix: '@@',
            basepath: '@file'
        }))
        .pipe(replace('PKG#VERSION', pkg.version))
        .pipe(replace('PKG#NAME', pkg.name))
        .pipe(gulp.dest(dist.html));
});


///////////////////////////////////////////////////////////////////////////////
// CSS Task
///////////////////////////////////////////////////////////////////////////////


gulp.task('css', function () {
    gulp.src([src.css])
        .pipe(concatCss(dist.css_file))
        .pipe(gulp.dest(dist.css));
});


///////////////////////////////////////////////////////////////////////////////
// Assets Task
///////////////////////////////////////////////////////////////////////////////


gulp.task('assets', function () {
    gulp.src([src.assets])
        .pipe(gulp.dest(dist.root));
});


///////////////////////////////////////////////////////////////////////////////
// Watch Task
///////////////////////////////////////////////////////////////////////////////


gulp.task('watch', function() {
    options.debug = true;
    process.env.NODE_ENV = null;
    gulp.run('default');
    gulp.watch(src.html, ['html']);
    gulp.watch(src.assets, ['assets']);
    gulp.watch(src.js, ['js']);
    gulp.watch(src.css, ['css']);
});


///////////////////////////////////////////////////////////////////////////////
// Default Task
///////////////////////////////////////////////////////////////////////////////


gulp.task('default', function () {
    process.env['NODE_ENV'] = 'production';

    return ['js', 'html', 'css', 'assets'];
}());
