'use strict';

var directionsDisplay;  /** type{google.maps.DirectionsRenderer} */
var directionsService = new google.maps.DirectionsService();
var distanceMatrixService = new google.maps.DistanceMatrixService();
var map;  /** type{google.maps.Map} Object describing visible map. */
var mode;  /** type{string} traveling mode.  e.g. 'DRIVING'. */
var start;  /** type{string} starting address */
var waypoints;  /** type{Array.<string>} list of other addresses */
var addresses;  /** type{Array.<string>} list of all addresses */
var costMatrix; /** type{Array.<Array.<number>>} travel cost matrix */
var costMatrixRows;  /** type{number} number of defined rows in costMatrix. */

/**
 * Called when the page is loaded and performs all needed initialization.
 */
function initialize() {
  directionsDisplay = new google.maps.DirectionsRenderer();
  var mapOptions = {
    center: new google.maps.LatLng(40.006756,-105.263618),  // C.U. Boulder
    zoom: 13
  };
  map = new google.maps.Map(document.getElementById('map-canvas'), mapOptions);
  directionsDisplay.setMap(map);
  directionsDisplay.setPanel(document.getElementById('directions-panel'));
}

/**
 * Listener that is called when the user clicks "Submit".
 *
 * This function computes the optimal route, displays it on a map, and
 * replaces the Destinations text area with the optimal route
 */
function calcRoute() {
  start = document.getElementById('startaddr').value;
  waypoints = document.getElementById('destaddr').value.split('\n');
  mode = "DRIVING";

  var radio_mode = document.getElementsByName('travelmode');
  for(var i=0; i<radio_mode.length; i++) {
    if(radio_mode[i].checked) {
      mode = radio_mode[i].value;
      break;
    }
  }

  // Strip off leading and trailing whitespace.
  waypoints = waypoints.map(function(value) {
    return value.replace(/^\s+/, '').replace(/\s+$/, '');
  });
  // Remove empty addresses.
  waypoints = waypoints.filter(function(value) { return value; });
  addresses = [start].concat(waypoints);
  var n = addresses.length;

  // If there are more than 10 addresses, we need to break this up into
  // multiple requests.  Rows correspond to origins.
  var maxRowsPerRequest = Math.min(Math.floor(100 / n), n);

  // Clear out matrix
  costMatrix = [];
  costMatrixRows = 0;
  for (var row=0; row < n; row += maxRowsPerRequest) {
    var dmRequest = {
      origins: addresses.slice(row, Math.min(row + maxRowsPerRequest, n)),
      destinations: addresses,
      travelMode: google.maps.TravelMode[mode]
    };
    console.log(dmRequest);

    distanceMatrixService.getDistanceMatrix(dmRequest,
        distanceMatrixCallback.bind(undefined, row));
  }
}

/**
 * Callback handler for a call to the distanceMatrix service.
 *
 * @param {number} row the index of the first row of the results.
 * @param {DistanceMatrixResponse} dmResponse matrix containing distances.
 * @param {DistanceMatrixStatus} dmStatus string status.  e.g. 'OK'.
 */
function distanceMatrixCallback(row, dmResponse, dmStatus) {
  console.log(dmResponse);
  console.log(dmStatus);
  // Save addresses with format provided by Google Maps
  addresses = dmResponse.destinationAddresses;
  document.getElementById('startaddr').value = addresses[0];
  var subMatrix = makeCostMatrix(dmResponse);
  for (var i = 0; i < subMatrix.length; i++) {
    costMatrix[i + row] = subMatrix[i];
  }
  costMatrixRows += subMatrix.length;

  // Send message to python server if we have all the rows back.
  if (costMatrixRows == addresses.length) {
    var requestObj = {
      'start': 1,
      'n': costMatrix.length,
      'travelMatrix': costMatrix,
    };
    if (document.getElementById('return').checked) {
      requestObj['end'] = 1;
    }
    var request = JSON.stringify(requestObj);
    console.log(request);

    // Send request to main server to solve the traveling salesperson problem.
    var http = new XMLHttpRequest();
    http.addEventListener('loadend', renderRoute, false);
    http.open("POST", "lpsolver/solver.request", true);
    http.setRequestHeader("Content-type", "application/json");
    http.send(request);
  }
}

/**
 * Renders the optimal route on the map
 *
 * @param {Event} e event object containing the response in '.target'.
 */
function renderRoute(e) {
  var response = e.target;
  if (response.status == 200) {
    var ordering = JSON.parse(response.response);
    console.log(ordering);
    var waypts = [];
    var orderingCount = ordering.length;
    var displayAddrs = []
    for (var i = 1; i < orderingCount-1; i++) {
      waypts.push({
        location: addresses[ordering[i]-1],
        stopover: true});
      displayAddrs.push(addresses[ordering[i]-1]);
    }
    var dest = addresses[ordering[orderingCount-1] - 1];
    if (!document.getElementById('return').checked) {
      displayAddrs.push(dest);
    }
    document.getElementById('destaddr').value = displayAddrs.join('\n');
    var request = {
      origin: addresses[0],
      destination: dest,
      waypoints: waypts,
      optimizeWaypoints: false,
      travelMode: google.maps.TravelMode[mode]
    };
    console.log(request);
    directionsService.route(request, function(response, status) {
      if (status == google.maps.DirectionsStatus.OK) {
        directionsDisplay.setDirections(response);
        document.getElementById('computed-route').style.display = 'block';
      }
    });
  } else {
    alert('Received response HTTP status ' + response.status);
  }
}

/**
 * Creates a simple cost matrix from the distanceMatrix response.
 *
 * @param{DistanceMatrixResponse} dmResponse.
 * @returns{Array.<Array.<number>>} cost matrix with origins in the rows
 *     and destinations in the columns.
 */
function makeCostMatrix(dmResponse) {
  var rows = dmResponse.rows;
  var matrix = [];
  for (var row = 0; row < rows.length; row++) {
    matrix[row] = [];
    var elements = rows[row].elements;
    for (var col = 0; col < elements.length; col++) {
      matrix[row][col] = elements[col].distance.value;
    }
  }
  return matrix;
}

function reset() {
    document.getElementById('computed-route').style.display = 'none';
    document.getElementById('startaddr').value = "";
    document.getElementById('destaddr').value = "";
    document.getElementById('return').checked = true;
    document.getElementById('drive').checked = true;
    document.getElementById('walk').checked = false;
    document.getElementById('cycle').checked = false;
    document.getElementById('startaddr').focus();
}

window.onresize = function(event) {
    if(window.outerHeight/screen.height < 0.96)
        document.getElementById('route-finder').style.overflow = 'auto';
    else
        document.getElementById('route-finder').style.overflow = '';
}
