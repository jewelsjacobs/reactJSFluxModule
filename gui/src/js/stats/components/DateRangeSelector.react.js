var React = require('react');
var Calendar = require('rc-calendar');
var Actions = require('../actions/ActionCreators');

var DateRangeSelector = React.createClass({

  handleFromDateChange: function(fromDate) {
    this.setState({
      fromDate: fromDate
    });
  },

 render: function() {

   return (
     <div id="between" className="rs-detail-value">
       <Calendar />
       and
       <Calendar />
     </div>
   );
 }
});

module.exports = DateRangeSelector;
