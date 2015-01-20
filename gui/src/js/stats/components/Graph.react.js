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

/**
 * Updates / creates the nvd3 graph
 *
 * @param data Dynamic state data which includes values and key. Consumed via Actions -> GraphStore -> API
 * @param replicaset prop that creates a dynamic id for the chart div
 * @private
 */
var _updateGraph = function (data, replicaset) {
  var graphData = [];

  /**
   * Maps API data schema to schema required by nvd3
   * @url https://github.com/novus/nvd3/blob/master/examples/lineChart.html
   */
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
      /**
       * GraphStore.getGraphState(this.props.replicaset)
       * returns graph data
       */
      return {data: GraphStore.getGraphState(this.props.replicaset)}
    },
    componentDidMount: function () {
      /**
       * Action which will send params to API and Dispatcher to get graph data
       */
      Actions.getGraphData(this.props.replicaset, this.props.statName, this.props.startDate, this.props.endDate, this.props.hosts);
      GraphStore.addChangeListener(this._onChange);
    },
    _onChange: function() {
      this.setState({data: GraphStore.getGraphState(this.props.replicaset)});
    },
    shouldComponentUpdate: function (nextProps, nextState) {

      if (nextState === this.state) {
        return false;
      } else {
        return true;
      }
    },
    render: function() {

      /**
       * Determines if graph data exists
       * @type {*|boolean}
       */
      var dataIsLoaded = _.has(this.state, "data")
                         && !_.isUndefined(this.state.data)
                         && !_.isEmpty(this.state.data);

      /**
       * Graph will not render until graph data exists
       */
      if (dataIsLoaded) {
        _updateGraph(this.state.data, this.props.replicaset);
        console.log(this.props.statName, this.props.startDate, this.props.endDate, this.state.data);
      };

      return (
        <div id={"chart1" + this.props.replicaset} >
          <svg></svg>
        </div>
      )
    }
  });

module.exports = Graph;
