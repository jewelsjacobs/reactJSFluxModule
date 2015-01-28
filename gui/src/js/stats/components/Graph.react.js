var React = require('react');
var Actions = require('../actions/ViewActionCreators.js');
var GraphStore = require('../stores/Graph.js');
var GraphHelpers = require('./helpers/GraphHelpers.js');
var DateRangeStore = require('../stores/DateRange.js');
var StatNameStore = require('../stores/StatName.js');
var LoaderHelpers = require('./helpers/LoaderHelpers.js');
var Loader = require('react-loader');
var moment = require('moment');
var _ = require('lodash');

/**
 * @author Julia Jacobs
 * @version 1.0.0
 * @description Graph component for nv3d graph.
 * @module components/graph
 * @type {*|Function}
 */

var Graph = React.createClass(
  {
    getInitialState: function() {
      return {
        data: GraphStore.getGraphState(this.props.replicaset),
        statName: StatNameStore.getStatName(),
        dates: DateRangeStore.getDateRange(),
        updateGraph: GraphStore.updateGraph(),
        isLoaded: GraphStore.isLoading()
      }
    },
    _onChange: function() {
      this.setState({
        data: GraphStore.getGraphState(this.props.replicaset),
        statName: StatNameStore.getStatName(),
        updateGraph: GraphStore.updateGraph(),
        dates: DateRangeStore.getDateRange(),
        isLoaded: GraphStore.isLoading()
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
      if (!_.isEqual(nextState, this.state)) {
        /**
         * When props change, inject them into action method to make an updated API call
         */
        var dates = (_.isNull(this.state.dates) || _.isUndefined(this.state.dates)) ?
                    {startDate : moment().subtract(1, 'day'), endDate : moment()} :
                    {startDate : this.state.dates.startDate, endDate : this.state.dates.endDate};

        var statName = _.isNull(nextState.statName) ? "mongodb.connections.current" : nextState.statName;

        if (!_.isEqual(nextState.updateGraph,this.state.updateGraph)) {
          Actions.getGraphData(
            this.props.replicaset,
            statName,
            dates.startDate,
            dates.endDate,
            this.props.shard.hosts
          );
        }
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
      return (
        <div id={"chart1" + this.props.replicaset} className="stats-graph">
            <Loader loaded={this.state.isLoaded} options={LoaderHelpers.spinnerOpts} />
            <svg></svg>
        </div>
      )
    }
  });

module.exports = Graph;
