$(document).ready(function() {
     $('div.shoutbox-history table tr:odd').addClass('odd');
     $('.edit').editable('/shout/edit/', {
         loadurl : '/shout/text/',
         indicator : 'Saving...',
         tooltip   : 'Click to edit your shout...',
         submit : 'OK',
         cancel : 'Cancel'
     });
     $('.shout-del').click(function () {
         if (confirm('Really delete this shout?')) {
             var id = this.id;
             if (id.match(/shout-del-(\d+)/)) {
                $.post('/shout/delete/', { id : RegExp.$1 }, function (id) {
                    var id = '#shout-del-' + id;
                    $(id).parents('tr').fadeOut(1500, function () {
                        $('div.shoutbox-history table tr:visible:even').removeClass('odd');
                        $('div.shoutbox-history table tr:visible:odd').addClass('odd');
                        });
                    }, 'text');
             }            
         }
         return false;
     });
 });
