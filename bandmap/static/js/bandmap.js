$(document).ready(function() {
   var map_div = $('#map-canvas');
   if (map_div.length) {
      var map_options = {
         center: {lat: 15.0, lng: -30.0},
         zoom: 2
      };
      var map = new google.maps.Map(map_div[0], map_options);
   }

   var add_form = $('#bandmap-add-form');
   if (add_form.length) {
   }
});
