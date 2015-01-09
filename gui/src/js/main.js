/** @jsx React.DOM */
'use strict';
/**
 * The application's entry point.
 *
 * TODO: When inline variables have been removed from jinja Templates
 *       We can render a base template component here or something
 */

  // Export React so the dev tools can find it
(window !== window.top ? window.top : window).React = React;

var Stats = require('./stats/components/Stats.react.js');
var React = require('react');
