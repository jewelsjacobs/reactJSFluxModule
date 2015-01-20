/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var Actions = require('../actions/ViewActionCreators.js');
var moment = require('moment');
var Graph = require('./Graph.react.js');

var GraphItems = React.createClass({
  getInitialState: function(){
    return {
      options: this.props.options
    }
  },
  componentDidMount: function(){
    this.setState({
     options: this.state.options
    })
  },
  componentWillReceiveProps: function(nextProps) {
    this.setState({
       options: nextProps.options
    }, console.log("updated"));
  },
  render: function() {
    var options = this.state.options;
    var startDate = options.startDate;
    var endDate = options.endDate;
    var statName = options.statName;
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
