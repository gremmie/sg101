$(document).ready(function() {
   var submit = $('#shoutbox-submit');
   submit.click(function () {
      var input = $('#shoutbox-smiley-input');
      var msg = input.val();
      msg = msg.replace(/^\s+/, '');
      msg = msg.replace(/\s+$/, '');
      if (msg.length == 0) {
         return false;
      }
      submit.attr('disabled', 'disabled');
      $.post('/shout/shout/', {
         msg: msg
         },
         function (data, textStatus) {
            input.val('');
            if (data != '') {
               $('#shoutbox-shout-container').prepend(data);
               $('#shoutbox-shout-container p:first').fadeIn(2500);
            }
            submit.removeAttr('disabled');
         },
         'html');
      return false;
   });
   var smilies_loaded = false;
   var smiley_frame = $('#shoutbox-smiley-frame');
   $('#shoutbox-smilies').click(function () {
      smiley_frame.toggle();
      if (!smilies_loaded) {
         smiley_frame.load('/smiley/farm/', function () {
            $('#shoutbox-busy-icon').hide();
            smilies_loaded = true;
         });
      }
   });
});

function sb_smiley_click(code)
{
    var txt = document.getElementById("shoutbox-smiley-input");
    txt.value += code;
    txt.focus();
}
