/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component used to generate multiple graphs.
 */
var React = require('react');
var Actions = require('../actions/ViewActionCreators.js');
var GraphStore = require('../stores/Graph.js');
var DateRangeStore = require('../stores/DateRange.js');
var StatNameStore = require('../stores/StatName.js');
var moment = require('moment');
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

      var numberOfPoints = stat.data.length;
      var skip = 1;

      if (numberOfPoints > 300) {
        skip = Math.floor(numberOfPoints / 300);
      }

      var reducedData = [];

      for (var i = 0; i < numberOfPoints; i = i + skip) {
        reducedData.push(stat.data[i]);
      }

      var values = [];

      _.forEach(reducedData, function(coordiantes){
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

    /**
     *  chart sub-models (ie. xAxis, yAxis, etc) when accessed directly,
     *  return themselves, not the parent chart, so need to chain separately
     */
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

    nv.utils.windowResize(chart.update);

    return chart;

  });
};

var Graph = React.createClass(
  {
    getInitialState: function() {
      return {
        data: GraphStore.getGraphState(this.props.replicaset),
        statName: StatNameStore.getStatName(),
        dates: DateRangeStore.getDateRange(),
        updateGraph: GraphStore.updateGraph()
      }
    },
    _onChange: function() {
      this.setState({
        data: GraphStore.getGraphState(this.props.replicaset),
        statName: StatNameStore.getStatName(),
        updateGraph: GraphStore.updateGraph(),
        dates: DateRangeStore.getDateRange()
      });
    },
    componentDidMount: function(){
      GraphStore.addChangeListener(this._onChange);
      StatNameStore.addChangeListener(this._onChange);
      DateRangeStore.addChangeListener(this._onChange);
    },
    componentWillUnmount: function() {
      GraphStore.removeChangeListener(this._onChange);
      StatNameStore.removeChangeListener(this._onChange);
      DateRangeStore.removeChangeListener(this._onChange);
    },
    shouldComponentUpdate: function (nextProps, nextState) {
      /**
       * When props change, inject them into action method to make an updated API call
       */
      var dates = (nextState.dates === null) ?
                  {startDate : moment().subtract(1, 'day'), endDate : moment()} :
                  {startDate : nextState.startDate, endDate : nextState.endDate};

      var statName = (nextState.statName === null) ? "mongodb.connections.current" : nextState.statName;

      if (nextState.updateGraph !== this.state.updateGraph) {
        Actions.getGraphData(
          this.props.replicaset,
          statName,
          dates.startDate,
          dates.endDate,
          this.props.shard.hosts
        );
      };

      if (!_.isEqual(nextState, this.state)) {

        /**
         * Determines if graph data exists
         * @type {*|boolean}
         */
        var dataIsLoaded = _.has(nextState, "data")
                           && !_.isUndefined(nextState.data)
                           && !_.isEmpty(nextState.data);

        /**
         * Graph will not render until graph data exists
         */
        if (dataIsLoaded) {
          _updateGraph(nextState.data, this.props.replicaset);
        };

      };
      return true;
    },
    render: function() {

      var svgComponent = function() {
        return (
          <svg></svg>
        )
      }.bind(this);

      /**
       * Determines if graph data exists
       * @type {*|boolean}
       */
      var dataIsLoaded = _.has(this.state, "data")
                         && !_.isUndefined(this.state.data)
                         && !_.isEmpty(this.state.data);

      return (
        <div id={"chart1" + this.props.replicaset} >
          { dataIsLoaded ? svgComponent() : null }
        </div>
      )
    }
  });

module.exports = Graph;
