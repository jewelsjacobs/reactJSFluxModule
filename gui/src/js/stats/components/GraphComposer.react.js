/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var MockDataStore = require('../stores/MockData.js');
var StatNames = require('./StatNames.react.js');
var Range = require('./Range.react.js');
var GraphItems = require('./GraphItems.react.js');

var GraphComposer = React.createclassName({
  getInitialState: function() {
    return {
      names : MockDataStore.getMockStatsNames(),
      shards : MockDataStore.getMockShardsAndHosts()
    };
  },
  componentDidMount: function() {
    this.setState(MockDataStore.getMockStatsNames());
    this.setState(MockDataStore.getMockShardsAndHosts());
  },
  render: function() {
    return (
      <div>
        <ul className="rs-detail-list">
          <StatNames names={this.state.names} />
          <li className="rs-detail-item">
            <Range />
          </li>
        </ul>
        <GraphItems shards={this.state.shards}/>
      </div>
    );
  }
});



module.exports = GraphComposer;
