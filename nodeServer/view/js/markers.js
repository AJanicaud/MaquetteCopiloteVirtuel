/* Caution: new marker inputs not sanitized
* Undefined behaviour if identical markers
* UPDATE: cannot create marker with same name (id) or exact same coordinates as another marker
*/

// GLOBAL VARIABLES-----------------------------------
var displayed_markers = [], // an array to store the markers displayed on the map
    map, // google.maps.Map object
    flightPath; // polyligne that define flight path to follow (diversion)
    // dict_markerLabels = new Map(), // associated stored marker(s) id(s) with displayed marker(s) label(s)

var current_location; // Google.maps.Marker object that indicates current location

// FUNCTIONS-----------------------------------------
// init map
function initMap() {
    // MAP DISPLAY options
    var options = {
        zoom: 10,
        center: {
            lat: 43.6042,
            lng: 1.4436
        },
        mapTypeId: 'terrain',
        mapTypeControl: true,
        mapTypeControlOptions: {
          style: google.maps.MapTypeControlStyle.button,
          mapTypeIds: ['satellite', 'terrain']
        }
    }

    // Create new map
    map = new google.maps.Map(document.getElementById('map'), options)
    current_location = new google.maps.Marker({
        map: map,
        animation: google.maps.Animation.DROP,
        position: {lat:43.4512507, lng:1.4464599},
        icon: '/img/plane_red.png',
        draggable: true
    });
    map.setCenter(current_location.getPosition());

    var markers = []
    localStorage.clear();

} //end initMap()

// Fetch markers
function fetchMarkers() {
  // Get markers from localStorage
  var markersResults = document.getElementById('markersResults');

  if (localStorage.getItem('markers') === null) {
        markersResults.innerHTML = '<p>No marker stored at the moment</p>';
        var markers = [];
    } else {
        // Get output id
        var markers = JSON.parse(localStorage.getItem('markers'));
        // Build output
        markersResults.innerHTML = '';
        for (var i = 0; i < markers.length; i++) {
              var content = markers[i].content;
              var lat = markers[i].coords.lat;
              var lng = markers[i].coords.lng;

              var hfcontent = content.replace('</h3>', '').replace('<h3>', '').replace(' ', '');
              markersResults.innerHTML += '<div class="well">' +
                  hfcontent +
                  ' <a onclick="deleteMarker(\'' + content + '\')" class="btn btn-danger" href="#">Delete</a> ' +
                  '</h3>' +
                  '<p>latitude: ' + lat + '<br>longitude: ' + lng + '</p>' +
                  '</div>';
          }
    }

  return markers;
}

// Add Marker Function
function addMarker(props, new_marker = true) {
    var already_exists = false;

    if (new_marker){
      // import saved markers from localstorage
      if (localStorage.getItem('markers') === null) {
            // Init array
            var markers = [];
        } else {
            // Get markers from localStorage
            var markers = JSON.parse(localStorage.getItem('markers'));
        }
      // Check if a marker with the same name (id) already exists in localStorage
      for (var i = 0; i < markers.length; i++) {
            if (markers[i].id == props.id) {
                  already_exists = true;
                  console.log('A marker named "' + props.id + '" already exists!');
              }
        }
      // Check if a marker with the exact same coordinates has already been displayed on map
      for (var i = 0; i < displayed_markers.length; i++) {
          if (displayed_markers[i].coords == props.coords) {
                already_exists = true;
                console.log('A marker with the exact same coordinates <lat:' + props.coords.lat + ' lng:' + props.coords.lng + '> has already been displayed on map!');
            }
        }
    }

    if (already_exists){
      // no action
      }else{
        // ADD marker to map
        var gmarker = new google.maps.Marker({
              position: props.coords,
              map: map,
              //icon:props.iconImage
          });
        displayed_markers.push(gmarker)

        // Check for customicon
        if (props.iconImage) {
              // Set icon image
              gmarker.setIcon(props.iconImage);
          }

        // Check content
        if (props.content) {
              disp = props.content + '<p>latitude: ' + props.coords.lat +
                  '<br>longitude: ' + props.coords.lng + '</p>';
              var infoWindow = new google.maps.InfoWindow({
                  content: disp
              });

              gmarker.addListener('click', function() {
                  infoWindow.open(map, gmarker);
              });
          }

        if (new_marker){
            // SAVE marker in localstorage
            markers.push(props);
            // Set to localStorage
            localStorage.setItem('markers', JSON.stringify(markers));

            // Re-fetch markers
            fetchMarkers();
          }
      }

      return gmarker;
}

//add polyligne that connects all subsequent markers two by two
function addPolyligne(listMarkers) {
  var flightPlanCoordinates = []
  for (let marker of listMarkers) {
    flightPlanCoordinates.push(marker.coords)
  }
  // remove old flight path from map
  if (flightPath){
    flightPath.setMap(null);
  }
  // define new flight path
  flightPath = new google.maps.Polyline({
    path: flightPlanCoordinates,
    geodesic: true,
    strokeColor: '#809650',
    strokeOpacity: 1.0,
    strokeWeight: 2
  });
  // add new flight path to map
  flightPath.setMap(map);
}

// Delete marker
function deleteMarker(content) {
    // Get markers from localStorage
    var markers = JSON.parse(localStorage.getItem('markers'));
    // Loop through markers
    for (var i = 0; i < markers.length; i++) {
          if (markers[i].content == content) {
                displayed_markers[i].setMap(null)
                // Remove marker from localstorage
                markers.splice(i, 1);
                // Remove marker for displayed_markers array
                displayed_markers.splice(i, 1);
            }
      }
    // Re-set back to localStorage
    localStorage.setItem('markers', JSON.stringify(markers));

    // Re-fetch markers
    fetchMarkers();
}

// FUNCTIONS called by client index.html
// tansmit current location on map
function getLocation(){
    latLng = {lat: current_location.getPosition().lat(),
              lng: current_location.getPosition().lng()};
    console.log('Current position: ' + JSON.stringify(latLng));
    return latLng;
}

//Update displayed location
function updateLocation(pointString){
    pos = JSON.parse(pointString);
    // update position on map
    current_location.setPosition(pos.coords);
    map.setCenter(current_location.getPosition());
    console.log('Current position updated: ' + JSON.stringify(pos.coords));
}

// Display markers on the maps from stringified list of markers
function displayMarkersFromList(listPointsString){
    console.log('Add markers: ' + listPointsString);
    var listPoints = JSON.parse(listPointsString);

    // Markers déjà sous format JSON
    GMAPS_markers = [];
    for (let marker of listPoints) {
        GMAPS_markers.push(addMarker(marker));
      }
    return GMAPS_markers;
}

// Remove markers on the maps from stringified list of markers
function removeMarkersFromList(listPointsString){
    console.log('Remove markers: ' + listPointsString);
    var listPoints = JSON.parse(listPointsString);

    // Markers déjà sous format JSON
    for (let marker of listPoints) {
        deleteMarker(marker.content);
      }
}

// Remove all markers (except current location)
function removeAllMarkers(){
    console.log('Remove all markers');
    var listMarkers = fetchMarkers();

    // Markers déjà sous format JSON
    for (let marker of listMarkers) {
        deleteMarker(marker.content);
      }

    if (localStorage.getItem('markers') !== null){
      console.log('[Error] Remaining markers: ' + localStorage.getItem('markers'));
      localStorage.clear();
    }
}

// Display polyligne from stringified list of markers
function drawPolyligneFromList(listPointsString){
    console.log('Draw Polyligne: ' + listPointsString);
    var listPoints = JSON.parse(listPointsString);
    // Markers déjà sous format JSON
    addPolyligne(listPoints);
    //Save polyligne ?
}
