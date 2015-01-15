/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var moment = require('moment');
var Actions = require('../actions/ViewActionCreators.js');
var GraphStore = require('../stores/Graph.js');
var _ = require('lodash');

var _options = {
  "type": "lineChart",
  "height": 300,
  "margin": {
    "top": 20,
    "right": 20,
    "bottom": 20,
    "left": 50
  },
  "useInteractiveGuideline": true,
  "transitionDuration": 250,
  "x": function (data) {
    return data[0];
  },
  "xAxis": {
    "staggerLabels": true,
    "tickFormat": function (data) {
      return d3.time.format('%m/%d/%y %X')(moment.unix(data).toDate());
    }
  },
  "y": function (data) {
    return data[1];
  }
};

var Graph = React.createClass({
  getInitialState: function() {
    return {data: []}
  },
  componentWillUnmount: function() {
    GraphStore.removeChangeListener(this._onChange);
  },
  componentDidMount: function() {
    GraphStore.addChangeListener(this._onChange);
    Actions.getGraphData(this.props.replicaset, this.props.statName, this.props.startDate, this.props.endDate, this.props.hosts);
  },
  _onChange: function(replicaset) {
    if (replicaset != this.props.replicaset) {
      return;
    }
    this.setState({data: GraphStore.getGraphState(this.props.replicaset)});
  },
  render: function() {
    /*These lines are all chart setup.  Pick and choose which chart features you want to utilize. */
    var graph = nv.addGraph(function() {
      var chart = nv.models.lineChart()
          .margin({left: _options.margin})  //Adjust chart margins to give the x-axis some breathing room.
          .useInteractiveGuideline(_options.useInteractiveGuideline)  //We want nice looking tooltips and a guideline!
          .transitionDuration(_options.transitionDuration)  //how fast do you want the lines to transition?
          .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
          .showYAxis(true)        //Show the y-axis
          .showXAxis(true);        //Show the x-axis

      chart.xAxis     //Chart x-axis settings
        .axisLabel(_options.x(''))
        .tickFormat(_options.xAxis.tickFormat());

      chart.yAxis     //Chart y-axis settings
        .axisLabel(_options.y(''));

      d3.select('#chart svg')    //Select the <svg> element you want to render the chart in.
        .datum(this.state.data)         //Populate the <svg> element with chart data...
        .call(chart);          //Finally, render the chart!

      return chart;
    }.bind(this));

    return (
      <div>
        {graph}
      </div>
    );
  }
});

module.exports = Graph;
