$(document).ready(function() {
   $('.gcal-del').click(function () {
      if (confirm('Really delete this event?')) {
         var id = this.id;
         if (id.match(/gcal-(\d+)/)) {
            $.ajax({
               url: '/calendar/delete/', 
               type: 'POST',
               data: { id : RegExp.$1 }, 
               dataType: 'text',
               success: function (id) {
                  var id = '#gcal-' + id;
                  $(id).parents('li').hide('normal');
               }, 
               error: function (xhr, textStatus, ex) {
                  alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
                     xhr.responseText);
               }
            });
         }
      }
      return false;
      });
});
