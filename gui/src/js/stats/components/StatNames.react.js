/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ActionCreators');

var StatNames = React.createclassName({
  getInitialState: function() {
    return {
      date: null
    };
  },
  handleChange: function(date) {
    this.setState({
      date: date
    });
  },
  render: function() {
    return (
      <li className="rs-detail-item">
        <div className="rs-detail-key">Stat:</div>
        <div className="rs-detail-value">
          <select ng-model="statName" ng-options="name for name in statNames">
            <option value="mongodb.opcounters.query">mongodb.opcounters.query</option>
          </select>
          <img id="load-stat-names" src="/static/art/loading.gif" alt="loading data" />
        </div>
      </li>
    );
  }
});

module.exports = StatNames;
