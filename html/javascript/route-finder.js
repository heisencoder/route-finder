/**
 * Called when the page is loaded and performs all needed initialization.
 */
function initialize() {
  var mapOptions = {
    center: new google.maps.LatLng(40.006756,-105.263618),
    zoom: 13
  };
  var map = new google.maps.Map(document.getElementById("map-canvas"),
      mapOptions);
}


