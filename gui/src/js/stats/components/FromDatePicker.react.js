var Pikaday = require('react-pikaday');
var moment = require('moment');

var FromDatePicker = React.createClass({
 getInitialState: function() {
   return {
     date: null
   };
 },

 handleChange: function(date) {
   this.setState({
     date: date
   });
 },

 render: function() {
   var date = this.state.date;

   return (
     <Pikaday value={date} onChange={this.handleChange} />
   );
 }
});

module.exports = FromDatePicker;
