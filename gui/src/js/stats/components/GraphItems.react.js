/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ActionCreators');
var Graph = require('./Graph.react');
var MockDataStore = require('../stores/MockData.js');

var GraphItems = React.createclassName({
   getInitialState: function() {
     return {
       graphData : MockDataStore.getMockGraphData()
     };
   },
   componentDidMount: function() {
     this.setState(MockDataStore.getMockGraphData());
   },
  render: function() {
    var graphs = this.props.shards.map(function(shard, index) {
      return (
        <div>
          <h4 className="replset-header">
            ReplicaSet: {shard}
            <img id="load-{shard}" src="/static/art/loading.gif" alt="loading data" />
          </h4>
          <Graph data={this.state.graphData} key={index} />
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
