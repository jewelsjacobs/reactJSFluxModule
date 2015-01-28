var React = require('react');
var Actions = require('../actions/ViewActionCreators.js');
var Graph = require('./Graph.react.js');
var _ = require('lodash');

/**
 * @author Julia Jacobs
 * @version 1.0.0
 * @description Component to render multiple rows of graphs
 * for all replicasets in an instance
 * @module components/graphitems
 * @type {*|Function}
 */

var GraphItems = React.createClass({
  render: function () {

    var graphItemsArray = [];

    _.forEach(this.props.shards, function (hosts, replicaset) {
      graphItemsArray.push({replicaset: replicaset, hosts: hosts});
    });

    var graphItems = graphItemsArray.map(function (graphItem, index) {
      return (
        <div key={index}>
          <h4 className="replset-header">
            ReplicaSet: {graphItem.replicaset}
          </h4>
          <Graph replicaset={graphItem.replicaset} shard={graphItem} />
        </div>
      );
    });

    return (
      <div>
      {graphItems}
      </div>
    );
  }
});

module.exports = GraphItems;
