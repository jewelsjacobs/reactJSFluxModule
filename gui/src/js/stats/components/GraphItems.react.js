/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ViewActionCreators.js');
var ShardsStore = require('../stores/Shards.js');
var Graph = require('./Graph.react.js');

var GraphItems = React.createClass({
  getInitialState: function() {
   return ShardsStore.getShardsState()
  },
  componentDidMount: function() {
    ShardsStore.addChangeListener(this._onChange);
  },
  componentWillUnmount: function() {
   ShardsStore.removeChangeListener(this._onChange);
  },
  _onChange: function() {
   this.setState(ShardsStore.getShardsState());
  },
  render: function() {
    var graphs = "";
    if (this.state !== null) {
      var graphs = this.state.data.map(
        function (stat, index) {
          var replicaset = Object.keys(stat)[0];
          return (
            <div key={index}>
              <h4 className="replset-header">
                ReplicaSet: {replicaset}
              </h4>
              <Graph data={stat} />
            </div>
          );
        });
    }
    return (
      <div>
        {graphs}
      </div>
    );
  }
});

module.exports = GraphItems;
