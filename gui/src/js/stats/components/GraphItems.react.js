/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ViewActionCreators.js');
var Graph = require('./Graph.react.js');

var GraphItems = React.createClass({
  render: function() {
    var options = this.props.options;
    var graphs = options.shards.map(
      function (stat, index) {
        var replicaset = Object.keys(stat)[0];
        return (
          <div key={index}>
            <h4 className="replset-header">
              ReplicaSet: {replicaset}
            </h4>
            <Graph replicaset={replicaset} hosts={stat[replicaset]} startDate={options.startDate} endDate={options.endDate} statName={options.statName} />
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
