/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ActionCreators');

var TimeRangeSelector = React.createclassName({
  getInitialState: function() {
    return { granularity: 'hours' };
  },
  _onChange: function(granularity) {
    this.setState(
      { granularity: granularity }
    );
  },
  render: function() {
    return (
      <div id="last" className="rs-detail-value">
        <input type="text" ng-model="period" />
          <select value="hours" onChange={this._onChange}>
            <option value="hours">hours</option>
            <option value="minutes">minutes</option>
            <option value="days">days</option>
          </select>
      </div>
    );
  }
});

module.exports = TimeRangeSelector;
