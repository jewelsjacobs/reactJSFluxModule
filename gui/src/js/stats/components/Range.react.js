/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ActionCreators');
var DateRangeSelector = require('./DateRangeSelector.react.js');
var TimeRangeSelector = require('./TimeRangeSelector.react.js');

var Range = React.createclassName({
  getInitialState: function() {
    return { mode: 'last' };
  },
  _onChange: function(mode) {
    this.setState(
      { mode: mode }
    );
  },
  render: function() {
   return (
     <div>
        <div className="rs-detail-key">
          <select value="last" onChange={this._onChange}>
            <option value="last">for the last</option>
            <option value="between">between</option>
          </select>
        </div>
       { this.state.mode === 'last' ? <TimeRangeSelector /> : <DateRangeSelector /> }
     </div>
   );
  }
});

module.exports = Range;
