$(document).ready(function() {
   $('.gcal-del').click(function () {
      if (confirm('Really delete this event?')) {
         var id = this.id;
         if (id.match(/gcal-(\d+)/)) {
            $.post('/calendar/delete/', { id : RegExp.$1 }, function (id) {
               var id = '#gcal-' + id;
               $(id).parents('li').hide('normal');
            }, 'text');
         }
      }
      return false;
   });
});
