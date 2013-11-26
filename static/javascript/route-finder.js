'use strict';
var directionsDisplay;
var directionsService = new google.maps.DirectionsService();
var distanceMatrixService = new google.maps.DistanceMatrixService();
var map;

/**
 * Called when the page is loaded and performs all needed initialization.
 */
function initialize() {
  directionsDisplay = new google.maps.DirectionsRenderer();
  var mapOptions = {
    center: new google.maps.LatLng(40.006756,-105.263618),
    zoom: 13
  };
  var map = new google.maps.Map(document.getElementById('map-canvas'),
      mapOptions);
  directionsDisplay.setMap(map);
}

function calcRoute() {
  var start = document.getElementById('startaddr').value;
  var waypoints = document.getElementById('destaddr').value.split('\n');
  // Strip off leading and trailing whitespace.
  waypoints = waypoints.map(function(value) {
    return value.replace(/^\s+/, '').replace(/\s+$/, '');
  });
  // Remove empty addresses.
  waypoints = waypoints.filter(function(value) { return value; });
  var addresses = [start].concat(waypoints);
  var dmRequest = {
    origins: addresses,
    destinations: addresses,
    travelMode: google.maps.TravelMode.DRIVING
  };
  console.log(addresses);

  distanceMatrixService.getDistanceMatrix(dmRequest,
      function(dmResponse, dmStatus) {
        console.log(dmResponse);
        console.log(dmStatus);
        var addresses = dmResponse.originAddresses;
        var matrix = makeJsonMatrix(dmResponse);
        var request = JSON.stringify({
          'start': 1,
          'n': matrix.length,
          'travelMatrix': matrix,
          'end': 1
        });
        console.log(request);
        var http = new XMLHttpRequest();
        http.addEventListener('loadend', function(e) {
          var response = e.target;
          if (response.status == 200) {
            var ordering = JSON.parse(response.response);
            console.log(ordering);
            var waypts = [];
            for (var i = 1; i < ordering.length; i++) {
              waypts.push({
                location: addresses[ordering[i] - 1],
                stopover: true});
            }
            var request = {
              origin: addresses[0],
              destination: addresses[0],
              waypoints: waypts,
              optimizeWaypoints: true,
              travelMode: google.maps.TravelMode.DRIVING
            };
            console.log(request);
            directionsService.route(request, function(response, status) {
              if (status == google.maps.DirectionsStatus.OK) {
                directionsDisplay.setDirections(response);
              }
            });
          }
        }, false);
        http.open("POST", "lpsolver/solver.request", true);
        http.setRequestHeader("Content-type", "application/json");
        http.send(request);
      });
  /*
  */
}

function makeJsonMatrix(dmResponse) {
  var rows = dmResponse.rows;
  var matrix = [];
  for (var row = 0; row < rows.length; row++) {
    matrix[row] = [];
    var elements = rows[row].elements;
    for (var col = 0; col < elements.length; col++) {
      matrix[row][col] = elements[col].duration.value;
    }
  }
  return matrix;
}
