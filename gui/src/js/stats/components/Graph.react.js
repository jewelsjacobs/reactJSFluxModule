/** @jsx React.DOM */
'use strict';
/**
 * The application component. This is the top-level component used to generate multiple graphs.
 * @TODO: Extract all of this messy coupled logic so this component can be easily be reused
 */
var React = require('react');
var Actions = require('../actions/ViewActionCreators.js');
var GraphStore = require('../stores/Graph.js');
var GraphHelpers = require('./helpers/GraphHelpers.js');
var DateRangeStore = require('../stores/DateRange.js');
var StatNameStore = require('../stores/StatName.js');
var moment = require('moment');
var _ = require('lodash');

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

      // load default graph options
      Actions.getGraphData(
        this.props.replicaset,
        "mongodb.connections.current",
        moment().subtract(1, 'day'),
        moment(),
        this.props.shard.hosts
      );
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
      var dates = (_.isNull(this.state.dates) || _.isUndefined(this.state.dates)) ?
                  {startDate : moment().subtract(1, 'day'), endDate : moment()} :
                  {startDate : this.state.dates.startDate, endDate : this.state.dates.endDate};

      var statName = _.isNull(nextState.statName) ? "mongodb.connections.current" : nextState.statName;

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
          GraphHelpers.updateGraph(nextState.data, this.props.replicaset);
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
