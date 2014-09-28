var bandmap = null;
var geocoder = null;
var surfbands = [];
var map_options = {
   center: {lat: 15.0, lng: -30.0},
   zoom: 2
};
var info_win = null;

function addBandOnSubmit(event) {
   var location = $('#id_location').val();
   if (!location) {
      alert("Please enter a location");
      return false;
   }
   var button = $(this);
   button.attr('disabled', 'disabled');
   var form = $('#bandmap-add-form');
   geocoder.geocode({'address': location}, function(results, status) {
      button.removeAttr('disabled');
      if (status == google.maps.GeocoderStatus.OK) {
         $('#id_lat').val(results[0].geometry.location.lat().toString());
         $('#id_lon').val(results[0].geometry.location.lng().toString());
         $(form).submit();
      }
      else {
         var msg = "Geocode unsuccessful: " + status + "\n" +
            "Enter a new location";
         alert(msg);
      }
   });
   return false;
}


function refreshMap() {
   bandmap.setOptions(map_options);
   $.each(surfbands, function(i, band) {
      band.marker.setMap(null);
   });
   surfbands.length = 0;
   var band_sel = $('#map-bands');
   band_sel[0].length = 0;
   band_sel.append($('<option>', {value: -1}).html('(select)'));
   var count_span = $('#map-band-count');
   count_span.html('0');
   var filter = $('#map-filter option:selected').val();

   $.getJSON('/bandmap/query/', {show: filter},
         function(data) {
            $.each(data, function(i, band) {
               band_sel.append($('<option>', {value: i, text: band.name}));
               var marker = new google.maps.Marker({
                  position: {lat: band.lat, lng: band.lon},
                  title: band.name,
                  map: bandmap
               });
               google.maps.event.addListener(marker, 'click', function() {
                  info_win.setContent(band.note);
                  info_win.open(bandmap, marker);
               });
               surfbands[i] = band;
               surfbands[i].marker = marker;
            });
            count_span.html(data.length);
         });
}

$(document).ready(function() {
   var map_div = $('#map-canvas');
   if (map_div.length) {
      bandmap = new google.maps.Map(map_div[0], map_options);
      info_win = new google.maps.InfoWindow();
      $('#map-filter-go').click(refreshMap);
      $('#map-bands').change(function() {
         var n = $('option:selected', this).val();
         if (n != -1) {
            info_win.setContent(surfbands[n].note);
            info_win.open(bandmap, surfbands[n].marker);
         }
      });
      refreshMap();
   }

   var add_form = $('#bandmap-add-form');
   if (add_form.length) {
      geocoder = new google.maps.Geocoder();
      $('#bandmap-add-submit').click(addBandOnSubmit);
   }
});
