$(document).ready(function() {
     $('div.shoutbox-history table tr:odd').addClass('odd');
     $('.edit').editable('/shout/edit/', {
         loadurl : '/shout/text/',
         indicator : 'Saving...',
         tooltip   : 'Click to edit your shout...',
         submit : 'OK',
         cancel : 'Cancel'
     });
     $('a.shout-del').click(function () {
         if (confirm('Really delete this shout?')) {
             var id = this.id;
             if (id.match(/^shout-del-(\d+)/)) {
                $.ajax({
                   url: '/shout/delete/', 
                   type: 'POST',
                   data: { id : RegExp.$1 }, 
                   dataType: 'text',
                   success: function (id) {
                    var id = '#shout-del-' + id;
                    $(id).parents('tr').fadeOut(1500, function () {
                        $('div.shoutbox-history table tr:visible:even').removeClass('odd');
                        $('div.shoutbox-history table tr:visible:odd').addClass('odd');
                        });
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
     $('.shout-flag').click(function () {
         var id = this.id;
         if (id.match(/^shout-flag-(\d+)/)) {
            id = RegExp.$1;
            if (confirm('Only flag a shout if you feel it is spam, abuse, violates site rules, ' +
                    'or is not appropriate. ' +
                    'A moderator will be notified and will review the shout. ' +
                    'Are you sure you want to flag this shout?')) {
                $.ajax({
                   url: '/shout/flag/', 
                   type: 'POST',
                   data: { id : id }, 
                   dataType: 'text',
                   success: function(response) {
                      alert(response);
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
