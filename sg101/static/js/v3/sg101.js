$(document).foundation();

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
   $('iframe').each(function(index) {
      $this = $(this);
      var src = $this.attr('src');
      var srcYouTube = src.includes('youtube');
      var srcVimeo = src.includes('vimeo');
      if (srcYouTube || srcVimeo) {
         var wrapper = $this.closest('div.flex-video');
         if (wrapper.length == 0) {
            var html = srcVimeo ? '<div class="flex-video vimeo"></div>'
                                : '<div class="flex-video"></div>';
            $this.wrap(html);
         }
      }
   });
});
