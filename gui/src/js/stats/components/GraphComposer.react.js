/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var BS = require('react-bootstrap');
var DateRangeSelector = require('./DateRangeSelector.react.js');
var StatNames = require('./StatNames.react.js');

var GraphComposer = React.createClass({
  render: function() {
    return (
      <BS.Grid>
        <BS.Row className="show-grid">
          <StatNames />
          <DateRangeSelector />
        </BS.Row>
      </BS.Grid>
    );
  }
});

module.exports = GraphComposer;
