/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('./stats/actions/ViewActionCreators.js');
var GraphItems = require('./stats/components/GraphItems.react.js');
var APIUtils = require('./stats/utils/APIUtils.js');
var GraphComposer = require('./stats/components/GraphComposer.react.js');
var ShardsStore = require('./stats/stores/Shards.js');

var Stats = React.createClass({
    getInitialState: function() {
      return ShardsStore.getShardsState();
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
        return (
          <div classNameName="stats-container">
            { this.state !== null ? <GraphComposer data={this.state.data}/> : null }
            { this.state !== null ? <GraphItems data={this.state.data} /> : null }
          </div>
        );
    }
});

var InstanceName = React.createClass({
  getInitialState: function() {
    return {
      instanceName : APIUtils.instanceName
    }
  },
  render: function() {
    return (
      <div className="rs-detail-header-title">{ this.state.instanceName }</div>
    );
  }
});

React.render(
  <InstanceName />,
  document.getElementById('instance-name')
);

React.render(
  <Stats />,
  document.getElementById('stats')
);

Actions.getShards();


