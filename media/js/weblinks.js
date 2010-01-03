$(document).ready(function() {
   $('a.weblinks-broken').click(function () {
      var id = this.id;
      if (id.match(/^link-(\d+)$/)) {
         id = RegExp.$1;
         if (confirm('Do you really want to report this link as broken? ' +
               'This will notify the site staff that the link is dead and that ' +
               'it may need to be deleted or revised.')) {
            $.ajax({
               url: '/links/report/' + id + '/',
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
