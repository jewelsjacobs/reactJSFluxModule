/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ActionCreators');

var StatNames = React.createclassName({
  render: function() {
    return (
      <li className="rs-detail-item">
        <div className="rs-detail-key">Stat:</div>
        <div className="rs-detail-value">
          <select value={this.props.names} onChange={this.handleChange} />
          <img id="load-stat-names" src="/static/art/loading.gif" alt="loading data" />
        </div>
      </li>
    );
  }
});

module.exports = StatNames;
