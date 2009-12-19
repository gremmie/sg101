var mmap = {
   map: null,
   geocoder: null,
   users: Object,
   userOnMap: false,
   userClick: function() {
      var name = $('option:selected', this).text();
      if (name != mmap.selectText)
      {
         mmap.clickUser(name);
      }
   },
   clickUser: function(name) {
      pt = new GLatLng(mmap.users[name].lat, mmap.users[name].lon);
      mmap.map.setCenter(pt);
      mmap.users[name].marker.openInfoWindowHtml(mmap.users[name].message);
   },
   clear: function() {
      mmap.users.length = 0;
   },
   selectText: "(select)",
   onMapDir: 'You have previously added yourself to the member map. Your information appears below. You may change ' +
      'the information if you wish. To delete yourself from the map, click the Delete button.',
   offMapDir: 'Your location is not on the map. If you would like to appear on the map, please fill out the form below ' +
      'and click the Submit button.'
};
$(document).ready(function() {
   if (GBrowserIsCompatible())
   {
      $(window).unload(GUnload);
      mmap.map = new GMap2($('#member_map_map')[0]);
      mmap.map.setCenter(new GLatLng(15.0, -30.0), 2);
      mmap.map.enableScrollWheelZoom();
      mmap.map.addControl(new GLargeMapControl());
      mmap.map.addControl(new GMapTypeControl());
      mmap.geocoder = new GClientGeocoder();

      if (mmapUser.userName)
      {
         $.getJSON('/member_map/query/', 
            function(data) {
               mmap.map.clearOverlays();
               var sel = $('#member_map_members');
               sel[0].length = 0;
               sel.append($('<option />').html(mmap.selectText));
               mmap.clear();
               $.each(data.users, function(i, item) {
                  sel.append($('<option />').html(item.name));
                  var marker = new GMarker(new GLatLng(item.lat, item.lon));
                  marker.bindInfoWindowHtml(item.message);
                  mmap.map.addOverlay(marker);
                  mmap.users[item.name] = item;
                  mmap.users[item.name].marker = marker;
                  if (mmapUser.userName == item.name)
                  {
                     mmap.userOnMap = true;
                  }
               });
               $('#member_map_count').html(data.users.length);

               sel = $('#member_map_recent');
               sel[0].length = 0;
               sel.append($('<option />').html(mmap.selectText));
               $.each(data.recent, function(i, item) {
                  sel.append($('<option />').html(item));
               });
               var submitButton = $('#member_map_submit');
               var deleteButton = $('#member_map_delete');

               submitButton.click(function() {
                  if (mmap.geocoder)
                  {
                     $(this).attr('disabled', 'disabled').val('Updating Map...');
                     var address = $('#id_location').val();
                     mmap.geocoder.getLatLng(address, 
                        function(point) { 
                           if (!point)
                           {
                              alert(address + ' could not be found on Google Maps.');
                              return;
                           }
                           $.ajax({
                              url: '/member_map/add/', 
                              type: 'POST',
                              data: {
                                 loc : address,
                                 lat : point.lat(),
                                 lon : point.lng(),
                                 msg : $('#id_message').val()
                              },
                              dataType: 'json',
                              success: function(data, textStatus) {
                                 var wasOnMap = mmap.userOnMap;
                                 if (mmap.userOnMap)
                                 {
                                    mmap.map.removeOverlay(mmap.users[mmapUser.userName].marker);
                                 }
                                 else
                                 {
                                    $('#member_map_members').append($('<option />').html(data.name));
                                    $('#member_map_recent').append($('<option />').html(data.name));
                                    mmap.userOnMap = true;
                                    deleteButton.removeAttr('disabled').val('Delete');
                                 }
                                 var marker = new GMarker(new GLatLng(data.lat, data.lon));
                                 marker.bindInfoWindowHtml(data.message);
                                 mmap.map.addOverlay(marker);
                                 mmap.users[mmapUser.userName] = data;
                                 mmap.users[mmapUser.userName].marker = marker;
                                 mmap.clickUser(mmapUser.userName);
                                 submitButton.removeAttr('disabled').val('Update');
                                 $('#member_map_directions').html(mmap.onMapDir);
                                 $('#member_map_count').html($('#member_map_members')[0].length - 1);
                                 alert(wasOnMap ? "Your location has been updated!" : 
                                       "You've been added to the map!");
                              },
                              error: function (xhr, textStatus, ex) {
                                 alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
                                    xhr.responseText);
                              }
                           });
                     });
                  }
                  return false;
               });

               deleteButton.click(function() {
                  deleteButton.attr('disabled', 'disabled').val('Deleting...');
                  $.ajax({ 
                     url: '/member_map/delete/', 
                     type: 'POST',
                     dataType: 'text',
                     success: function(data, textStatus) {
                        $('#id_location').val('');
                        $('#id_message').val('');
                        $("#member_map_members option[value='" + mmapUser.userName + "']").remove();
                        $("#member_map_recent option[value='" + mmapUser.userName + "']").remove();
                        mmap.map.removeOverlay(mmap.users[mmapUser.userName].marker);
                        mmap.users[mmapUser.userName].marker = null;
                        mmap.users[mmapUser.userName] = null;
                        mmap.userOnMap = false;
                        deleteButton.val('Delete');
                        submitButton.removeAttr('disabled').val('Add');
                        $('#member_map_directions').html(mmap.offMapDir);
                        $('#member_map_count').html($('#member_map_members')[0].length - 1);
                        alert("You've been removed from the map.");
                     },
                     error: function (xhr, textStatus, ex) {
                        alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
                           xhr.responseText);
                     }
                  });
                  return false;
               });
               
               if (mmap.userOnMap)
               {     
                  submitButton.val('Update');
                  $('#member_map_directions').html(mmap.onMapDir);
               }
               else
               {
                  submitButton.val('Add');
                  deleteButton.attr('disabled', 'disabled');
                  $('#member_map_directions').html(mmap.offMapDir);
               }
         });
         $('#member_map_members').change(mmap.userClick);
         $('#member_map_recent').change(mmap.userClick);
      }
   }
});
