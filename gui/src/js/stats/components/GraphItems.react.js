/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ActionCreators.js');
var StatsNamesStore = require('../stores/StatsNames.js');
var Graph = require('./Graph.react.js');

function getStatsNamesState() {
  return {
    stats: this.prop.shardsAndReplicaSets
  };
}

var GraphItems = React.createClass({
  getInitialState: function() {
   return getStatsNamesState();
  },
  componentDidMount: function() {
   StatsNamesStore.addChangeListener(this._onChange);
  },
  componentWillUnmount: function() {
   StatsNamesStore.removeChangeListener(this._onChange);
  },
  /**
  * Event handler for 'change' events coming from the stores
  */
  _onChange: function() {
   this.setState(getStatsNamesState());
  },
  render: function() {
    console.log(this.state);
    var graphs = this.state.stats.map(function(stat, index) {
      console.log(stat, index);
      return (
        <div key={index}>
          //<h4 className="replset-header">
          //  ReplicaSet: {stat.host_name}
          //</h4>
          //<Graph data={stat.data} />
        </div>
      );
    });
    return (
      <div>
        {graphs}
      </div>
    );
  }
});

module.exports = GraphItems;
