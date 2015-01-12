/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ActionCreators.js');
var Graph = require('./Graph.react.js');
var MockDataStore = require('../stores/MockData.js');

var GraphItems = React.createClass({
   getInitialState: function() {
     return {
       stats : MockDataStore.graphData.stats
     };
   },
   componentDidMount: function() {
     this.setState(
       {
         stats : MockDataStore.graphData.stats
       }
     );
   },
  render: function() {
    console.log(this.state.stats);
    var graphs = this.state.stats.map(function(stat, index) {
      return (
        <div key={index}>
          <h4 className="replset-header">
            ReplicaSet: {stat.host_name}
          </h4>
          <Graph data={stat.data} />
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
