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

var _updateGraph = function (data, replicaset) {
  var graphData = [];

  data.stats.map(
    function (stat, index) {

      var values = [];
      _.forEach(stat.data, function(coordiantes){
        values.push({x: coordiantes[0], y: coordiantes[1]});
      });

      graphData.push({
        values: values,      //values - represents the array of {x,y} data points
        key: stat["host_name"] //key  - the name of the series.
      });
    });

  var chart;

  nv.addGraph(function() {
    chart = nv.models.lineChart()
      .options({
       margin: {
         top: 20,
         right: 50,
         bottom: 50,
         left: 50
       },
       x: function (d, i) {
         return d.x;
       },
       y: function (d, i) {
         return d.y;
       },
       showXAxis: true,
       showYAxis: true,
       transitionDuration: 250,
       useInteractiveGuideline: true
     });

    // chart sub-models (ie. xAxis, yAxis, etc) when accessed directly, return themselves, not the parent chart, so need to chain separately
    chart.xAxis
      .axisLabel("")
      .staggerLabels(true)
      .tickFormat(function (data) {
        return d3.time.format('%m/%d/%y %X')(moment.unix(data).toDate());
      });

    chart.yAxis
      .axisLabel("");

    d3.select('#chart1' + replicaset + ' svg')
      .datum(graphData)
      .call(chart);

    //TODO: Figure out a good way to do this automatically
    nv.utils.windowResize(chart.update);

    return chart;

  });
};

var Graph = React.createClass(
  {
    getInitialState: function() {
      return {data: GraphStore.getGraphState(this.props.replicaset)}
    },
    componentDidMount: function () {
      var dataIsLoaded = _.has(this.state, "data")
                         && !_.isUndefined(this.state.data)
                         && !_.isEmpty(this.state.data);
      Actions.getGraphData(this.props.replicaset, this.props.statName, this.props.startDate, this.props.endDate, this.props.hosts);
      GraphStore.addChangeListener(this._onChange);
      if (dataIsLoaded) {
        _updateGraph(this.state.data, this.props.replicaset);
      }
    },
    _onChange: function() {
      this.setState({data: GraphStore.getGraphState(this.props.replicaset)});
    },
    shouldComponentUpdate: function (props) {
      var dataIsLoaded = _.has(this.state, "data")
                         && !_.isUndefined(this.state.data)
                         && !_.isEmpty(this.state.data);
      Actions.getGraphData(props.replicaset, props.statName, props.startDate, props.endDate, props.hosts);
      if (dataIsLoaded) {
        _updateGraph(this.state.data, props.replicaset);
      }
      return false;
    },
    render: function() {
      return (
        <div id={"chart1" + this.props.replicaset} >
          <svg></svg>
        </div>
      )
    }
  });

module.exports = Graph;
