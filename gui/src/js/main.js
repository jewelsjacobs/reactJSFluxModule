/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
//var GraphComposer = require('./stats/components/GraphComposer.react.js');
var Actions = require('./stats/actions/ActionCreators.js');
var GraphItems = require('./stats/components/GraphItems.react.js');
var APIUtils = require('./stats/utils/APIUtils.js');
var GraphComposer = require('./stats/components/GraphComposer.react.js');

var Stats = React.createClass({
    render: function() {
        return (
          <div classNameName="stats-container">
            <GraphComposer />
            <GraphItems />
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


