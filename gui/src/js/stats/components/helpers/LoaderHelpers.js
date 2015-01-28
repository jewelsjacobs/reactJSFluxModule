/**
 * @author Julia Jacobs
 * @version 1.0.0
 * @description Helper methods for the react-loader Component
 * @module helpers/loaderhelpers
 * @link {https://github.com/quickleft/react-loader}
 * @type {{spinnerOpts: {lines: number, length: number, width: number, radius: number, corners: number, rotate: number, direction: number, color: string, speed: number, trail: number, shadow: boolean, hwaccel: boolean, zIndex: number, top: string, left: string}}}
 */

var LoaderHelpers = {
  spinnerOpts: {
    lines: 13, // The number of lines to draw
    length: 20, // The length of each line
    width: 10, // The line thickness
    radius: 30, // The radius of the inner circle
    corners: 1, // Corner roundness (0..1)
    rotate: 0, // The rotation offset
    direction: 1, // 1: clockwise, -1: counterclockwise
    color: '#000', // #rgb or #rrggbb or array of colors
    speed: 1, // Rounds per second
    trail: 60, // Afterglow percentage
    shadow: false, // Whether to render a shadow
    hwaccel: false, // Whether to use hardware acceleration
    zIndex: 2e9, // The z-index (defaults to 2000000000)
    top: 'auto', // Top position relative to parent in px
    left: 'auto' // Left position relative to parent in px
  }
};

module.exports = LoaderHelpers;
