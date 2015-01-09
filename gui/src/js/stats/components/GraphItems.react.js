/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ActionCreators');

var GraphItems = React.createclassName({

  render: function() {
    return (
      <div ng-if="statName !== ''">
        <div ng-repeat="(shardName, hosts) in shards" ng-controller="StatsGraphCtrl">
        <h4 className="replset-header">
          ReplicaSet: {this.props.shard-name}
          <img id="load-{this.props.shard-name}" src="/static/art/loading.gif" alt="loading data" />
        </h4>
          <div ng-if="data !== undefined">
          <nvd3 options="options" data="data" config="{autorefresh: true, refreshDataOnly: true}"></nvd3>
          </div>
        </div>
      </div>
    );
  }
});

module.exports = GraphItems;
