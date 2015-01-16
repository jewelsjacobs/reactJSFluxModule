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

var Graph = React.createClass({
  getInitialState: function() {
    return {data: GraphStore.getGraphState(this.props.replicaset)}
  },
  componentWillUnmount: function() {
    GraphStore.removeChangeListener(this._onChange);
  },
  componentDidMount: function() {
    GraphStore.addChangeListener(this._onChange);
    Actions.getGraphData(this.props.replicaset, this.props.statName, this.props.startDate, this.props.endDate, this.props.hosts);
  },
  _onChange: function() {
    this.setState({data: GraphStore.getGraphState(this.props.replicaset)});
  },
  render: function() {
    if (this.state.hasOwnProperty("data") && typeof this.state.data != "undefined") {
      var data = [];

      this.state.data.stats.map(
        function (stat, index) {

          var values = [];
          _.forEach(stat.data, function(coordiantes){
            values.push({x: coordiantes[0], y: coordiantes[1]});
          });

          data.push({
            values: values,      //values - represents the array of {x,y} data points
            key: stat["host_name"] //key  - the name of the series.
          });
      });

      var replicaset = this.props.replicaset;

      /*These lines are all chart setup.  Pick and choose which chart features you want to utilize. */
      var chart;

      nv.addGraph(function() {
        chart = nv.models.lineChart()
          .options({
             margin: {
               top: 20,
               right: 20,
               bottom: 20,
               left: 50
             },
             x: function (d, i) {
               return i;
             },
             y: function (d, i) {
               return i;
             },
             showXAxis: true,
             showYAxis: true,
             transitionDuration: 250,
             useInteractiveGuideline: true
           });

        // chart sub-models (ie. xAxis, yAxis, etc) when accessed directly, return themselves, not the parent chart, so need to chain separately
        chart.xAxis
          .axisLabel("")
          .tickFormat(d3.format(',.1f'));

        chart.yAxis
          .axisLabel("")
          .tickFormat(d3.format(',.2f'));

        d3.select('#chart1' + replicaset + ' svg')
          .datum(data)
          .call(chart);

        //TODO: Figure out a good way to do this automatically
        nv.utils.windowResize(chart.update);
        //nv.utils.windowResize(function() { d3.select('#chart1 svg').call(chart) });

        chart.dispatch.on('stateChange', function(e) { nv.log('New State:', JSON.stringify(e)); });

        return chart;
      });
    };

    var svgStyle = {
      height: '500px'
    };

    return (
      <div id={"chart1" + this.props.replicaset} >
        <svg style={svgStyle}></svg>
      </div>
    );
  }
});

module.exports = Graph;
