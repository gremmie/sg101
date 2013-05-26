$(document).ready(function() {
   $.ajaxSetup({
       beforeSend: function(xhr, settings) {
           function getCookie(name) {
               var cookieValue = null;
               if (document.cookie && document.cookie != '') {
                   var cookies = document.cookie.split(';');
                   for (var i = 0; i < cookies.length; i++) {
                       var cookie = jQuery.trim(cookies[i]);
                       // Does this cookie string begin with the name we want?
                       if (cookie.substring(0, name.length + 1) == (name + '=')) {
                           cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                           break;
                       }
                   }
               }
               return cookieValue;
           }
           if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
               // Only send the token to relative URLs i.e. locally.
               xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
           }
       }
   });

   // social bookmarking pop-up support
   $('.social-sharing').delegate('a', 'click', function(e) {
      if ($(window).width() > 700)
      {
         e.preventDefault();
         window.open(this.href,'share-this','height=300,width=500,status=no,toolbar=no');
      }
   });

   $("html").bind("ajaxStart", function() {
      $(this).addClass('busy');
   }).bind("ajaxStop", function() {
      $(this).removeClass('busy');
   });

   var numShouts = $('#shoutbox-shout-container > p').size(); 
   var sbBox = $('#shoutbox-shout-container');

   if (numShouts < 2)
   {
      sbBox.append('<p>Welcome to SurfGuitar101.com!</p>');
      ++numShouts;
   }
   if (numShouts < 2)
   {
      sbBox.append('<p>((((( More Reverb )))))</p>');
      ++numShouts;
   }

   var sbCycleOpts = null;
   var sbCycle = sbBox.cycle({
      fx: 'scrollUp',
      timeout: 5000,
      pause: 1,
      next: '#shoutbox-next',
      prev: '#shoutbox-prev',
      before: function(curr, next, opts) {
         if (!opts.addSlide || sbCycleOpts) return;
         sbCycleOpts = opts;
      }
   });
   function addShout(shout) {
      ++numShouts;
      sbCycleOpts.addSlide(shout);
      sbBox.cycle(numShouts - 1);
   }

   var submit = $('#shoutbox-submit');
   submit.click(function () {
      var input = $('#shoutbox-smiley-input');
      var msg = $.trim(input.val());
      if (msg.length == 0) {
         return false;
      }
      submit.attr('disabled', 'disabled');
      $.ajax({
         url: '/shout/shout/', 
         type: 'POST',
         data: { msg: msg },
         dataType: 'html',
         success: function (data, textStatus) {
            input.val('');
            if (data != '') {
               addShout(data);
            }
            submit.removeAttr('disabled');
         },
         error: function (xhr, textStatus, ex) {
             alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
                xhr.responseText);
         }
      });
      return false;
   });
   var smilies_loaded = false;
   var smiley_frame = $('#shoutbox-smiley-frame');
   $('#shoutbox-smilies').click(function () {
      smiley_frame.toggle();
      if (!smilies_loaded) {
         smiley_frame.load('/smiley/farm/', function () {
            $('#shoutbox-busy-icon').hide();
            var txt = $("#shoutbox-smiley-input")[0];
            $('#shoutbox-smiley-frame img').click(function() {
               txt.value += ' ' + this.alt + ' ';
               txt.focus();
            });
            smilies_loaded = true;
         });
      }
   });
});
