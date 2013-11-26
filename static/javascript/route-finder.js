var directionsDisplay;
var directionsService = new google.maps.DirectionsService();
var map;

/**
 * Called when the page is loaded and performs all needed initialization.
 */
initialize = function() {
  directionsDisplay = new google.maps.DirectionsRenderer();
  var mapOptions = {
    center: new google.maps.LatLng(40.006756,-105.263618),
    zoom: 13
  };
  var map = new google.maps.Map(document.getElementById("map-canvas"),
      mapOptions);
  directionsDisplay.setMap(map);
}

calcRoute = function() {
  var start = document.getElementById('startaddr').value;
  var end = document.getElementById('destaddr').value;
  var request = {
      origin:start,
      destination:end,
      travelMode: google.maps.TravelMode.DRIVING
  };
  directionsService.route(request, function(response, status) {
    if (status == google.maps.DirectionsStatus.OK) {
      directionsDisplay.setDirections(response);
    }
  });
}
