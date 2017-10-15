'use strict';


function loadLibraries () {
    window.jQuery = require('jquery');
    window.$ = window.jQuery;
    window.angular = require('angular');
}


function loadApplication () {
    require('./lib/index.js');
    require('./service/index.js');
    require('./controller/index.js');
}


window.onload = function () {
    loadLibraries();
    loadApplication();
};
