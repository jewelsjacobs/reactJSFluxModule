var React = require('react');
var ToDatePicker = require('./ToDatePicker.react.js');
var FromDatePicker = require('./ToDatePicker.react.js');
var Actions = require('../actions/ActionCreators');

var DateRangeSelector = React.createClass({
 getInitialState: function() {
   return {
     toDate: null,
     fromDate: null
   };
 },

 handleToDateChange: function(toDate) {
   this.setState({
     toDate: toDate
   });
 },

  handleFromDateChange: function(fromDate) {
    this.setState({
      fromDate: fromDate
    });
  },

 render: function() {
   var toDate = this.state.toDate;
   var fromDate = this.state.fromDate;

   return (
     <div id="between" className="rs-detail-value">
       <ToDatePicker value={fromDate} onChange={this.handleFromDateChange} />
       and
       <FromDatePicker value={toDate} onChange={this.handleToDateChange} />
     </div>
   );
 }
});

module.exports = DateRangeSelector;
