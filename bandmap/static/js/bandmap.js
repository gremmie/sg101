var bandmap = null;
var geocoder = null;

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

$(document).ready(function() {
   var map_div = $('#map-canvas');
   if (map_div.length) {
      var map_options = {
         center: {lat: 15.0, lng: -30.0},
         zoom: 2
      };
      bandmap = new google.maps.Map(map_div[0], map_options);
   }

   var add_form = $('#bandmap-add-form');
   if (add_form.length) {
      geocoder = new google.maps.Geocoder();
      $('#bandmap-add-submit').click(addBandOnSubmit);
   }
});
