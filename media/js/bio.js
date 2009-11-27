$(document).ready(function() {
   var bday = $('#id_birthday');
   // jquery ui may not always be loaded
   if (bday.length) {
      bday.datepicker({changeMonth: true, 
         changeYear: true,
         dateFormat: 'yy-mm-dd',
         defaultDate: '-30y',
         minDate: new Date(1909, 0, 1),
         maxDate: new Date(),
         yearRange: '-100:+0'});
   }
   $('a.profile-flag').click(function() {
      var id = this.id;
      if (id.match(/fp-(\d+)/)) {
         id = RegExp.$1;
         if (confirm('Only report a profile if you feel it is spam, abuse, ' +
                 'violates site rules, or is not appropriate. ' +
                 'A moderator will be notified and will review the profile. ' +
                 'Are you sure you want to report this profile?')) {
             $.ajax({
               url: '/profile/flag/' + id + '/',
               type: 'POST',
               dataType: 'text',
               success: function (response, textStatus) {
                  alert(response);
               },
               error: function (xhr, textStatus, ex) {
                  alert('Oops, an error occurred: ' + xhr.statusText + ' - ' + xhr.responseText);
               }
             });
         }
     }
     return false;
   });
});
