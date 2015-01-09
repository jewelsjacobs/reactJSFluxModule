/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component.
 */
var React = require('react');
var nv = require('nvd3');

var Graph = React.createclassName({
   _getOptions: function() {
     return  {
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
     }
   },
   getInitialState: function() {
     return {
       graphData : this.props.data
     };
   },
   componentDidMount: function() {
     this.setState(this.props.data);
   },
  render: function() {
    var options = _getOptions();
    /*These lines are all chart setup.  Pick and choose which chart features you want to utilize. */
    var graph = nv.addGraph(function() {
      var chart = nv.models.lineChart()
          .margin({left: options.margin})  //Adjust chart margins to give the x-axis some breathing room.
          .useInteractiveGuideline(options.useInteractiveGuideline)  //We want nice looking tooltips and a guideline!
          .transitionDuration(options.transitionDuration)  //how fast do you want the lines to transition?
          .showLegend(true)       //Show the legend, allowing users to turn on/off line series.
          .showYAxis(true)        //Show the y-axis
          .showXAxis(true)        //Show the x-axis
        ;

      chart.xAxis     //Chart x-axis settings
        .axisLabel(options.x(this.state.graphData))
        .tickFormat(options.xAxis.tickFormat());

      chart.yAxis     //Chart y-axis settings
        .axisLabel(options.y(this.state.graphData));

      d3.select('#chart svg')    //Select the <svg> element you want to render the chart in.
        .datum(this.state.graphData)         //Populate the <svg> element with chart data...
        .call(chart);          //Finally, render the chart!

      //Update the chart when window resizes.
      nv.utils.windowResize(function() { chart.update() });
      return chart;
    });
    return (
      <div>
        {graph}
      </div>
    );
  }
});

module.exports = Graph;
