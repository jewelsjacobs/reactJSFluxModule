/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component used to generate multiple graphs.
 */
var moment = require('moment');
var _ = require('lodash');

var GraphHelpers = {
  /**
   * Updates / creates the nvd3 graph
   * @param data
   * @param replicaset
   */
  updateGraph : function (data, replicaset) {
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
  }
};

module.exports = GraphHelpers;
