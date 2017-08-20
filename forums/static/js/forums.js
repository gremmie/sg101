$(document).ready(function() {
   var postText = $('#id_body');
   var postButton = $('#forums-reply-post');
   postButton.click(function () {
      $(this).attr('disabled', 'disabled').val('Posting reply...');

      var attachments = new Array()
      $('#attachment div input').each(function(index) {
         attachments[index] = $(this).val();
      });

      $.ajax({
         url: '/forums/quick-reply/',
         type: 'POST',
         data: {
            body : postText.val(),
            topic_id : $('#id_topic_id').val(),
            attachment : attachments
         },
         traditional: true,
         dataType: 'html',
         success: function (data, textStatus) {
            postText.val('');
            var lastPost = $('#forum-topic-post-container > div:last-child');
            var firstCard = lastPost.find('div > div').first();
            var newCardClass = firstCard.hasClass('sg101-card1') ? 'sg101-card2' : 'sg101-card1';
            var newDividerClass = newCardClass == 'sg101-card1' ? 'sg101-card-divider1' : 'sg101-card-divider2';
            lastPost.after(data);

            lastPost = $('#forum-topic-post-container > div:last-child');
            var firstCard = lastPost.find('> div > div').first();
            firstCard.addClass(newCardClass);
            var firstDivider = firstCard.find('> div').first();
            firstDivider.addClass(newDividerClass);
            var lastCard = lastPost.find('> div:last-child > div').first();
            lastCard.addClass(newCardClass);
            var lastDivider = lastCard.find('> div').first();
            lastDivider.addClass(newDividerClass);

            lastPost.hide();
            lastPost.fadeIn(3000);
            postButton.removeAttr('disabled').val('Submit Reply');
            initAttachments();
         },
         error: function (xhr, textStatus, ex) {
            alert('Oops, an error occurred. ' + xhr.statusText + ' - ' +
               xhr.responseText);
            postButton.removeAttr('disabled').val('Submit Reply');
            initAttachments();
         }
         });
      return false;
   });
   $('a.post-flag').click(function () {
      var id = this.id;
      if (id.match(/fp-(\d+)/)) {
         id = RegExp.$1;
         if (confirm('Only flag a post if you feel it is spam, abuse, violates site rules, ' +
                 'or is not appropriate. ' +
                 'A moderator will be notified and will review the post. ' +
                 'Are you sure you want to flag this post?')) {
             $.ajax({
               url: '/forums/flag-post/',
               type: 'POST',
               data: {id: id},
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
   $('a.post-delete').click(function () {
      var id = this.id;
      if (id.match(/dp-(\d+)/)) {
         id = RegExp.$1;
         if (confirm('Are you sure you want to delete this post?')) {
             $.ajax({
               url: '/forums/delete-post/',
               type: 'POST',
               data: {id: id},
               dataType: 'text',
               success: function (response, textStatus) {
                  alert(response);
                  $('#post-' + id).fadeOut(3000);
               },
               error: function (xhr, textStatus, ex) {
                  alert('Oops, an error occurred: ' + xhr.statusText + ' - ' + xhr.responseText);
               }
             });
         }
     }
     return false;
   });
   $('#forum-mod-del-topic').click(function () {
         return confirm('Are you sure you want to delete this topic?\n' +
            'WARNING: all posts will be lost.');
   });

   var vid = 0;
   var vidDiv = $('#attachment');

   function clearAttachments()
   {
      $('#attachment div').remove();
      $('#attach-another').remove();
   }

   function processEmbeds(data, textStatus)
   {
      vidDiv.find('img').remove();
      $.each(data, function(index, value) {
         var html = '<div id="video-' + index + '">' + value.html +
            '<span class="link">' +
            '<img src="/static/icons/television_delete.png" alt="Remove" /> ' +
            '<a href="#">Remove</a></span>' +
            '<input type="hidden" name="attachment" value="' + value.id + '" />';
            '</div>';
         vidDiv.append(html);
         $('#video-' + index + ' a').click(function() {
            $('#video-' + index).remove();
            relabelAttachLink();
            return false;
         });
      });
      vid = data.length;
      $('#video-' + (vid-1)).after('<a id="attach-another" href="#">Attach another video</a>');
      $('#attach-another').click(function() {
         addVideo();
         relabelAttachLink();
         return false;
      });
   }

   function initAttachments()
   {
      clearAttachments();

      var post_input = $('#id_post_id');
      var attachments = $("#forums_post_form input:hidden[name='attachment']");
      if (post_input.length == 1)
      {
         post_id = post_input.val();
         vidDiv.prepend('<img src="/static/icons/ajax_busy.gif" alt="Busy" />');
         $.ajax({
            url: '/forums/fetch_attachments/',
            type: 'GET',
            data: {
               pid : post_id
            },
            dataType: 'json',
            success: processEmbeds,
            error: function (xhr, textStatus, ex) {
               vidDiv.find('img').remove();
               alert('Oops, an error occurred. ' + xhr.statusText + ' - ' +
                  xhr.responseText);
            }
         });
      }
      else if (attachments.length > 0)
      {
         vidDiv.prepend('<img src="/static/icons/ajax_busy.gif" alt="Busy" />');
         var embeds = new Array();
         attachments.each(function(index) {
            embeds[index] = $(this).val();
         });
         attachments.remove();
         $.ajax({
            url: '/oembed/fetch_saved/',
            type: 'GET',
            data: {
               embeds: embeds
            },
            traditional: true,
            dataType: 'json',
            success: processEmbeds,
            error: function (xhr, textStatus, ex) {
               vidDiv.find('img').remove();
               alert('Oops, an error occurred. ' + xhr.statusText + ' - ' +
                  xhr.responseText);
            }
         });
      }
      else
      {
         vid = 0;
         var s = '<div id="init-add">' +
                     '<button class="button">' +
                        '<i class="fi-video"></i> Attach Video' +
                     '</button>' +
                 '</div>';
         vidDiv.prepend(s);
         $('#attachment button').click(function () {
            $('#init-add').remove();
            addVideo();
            return false;
         });
      }
   }

   function relabelAttachLink()
   {
      var another = $('#attach-another');
      var n = $('#attachment div').length;
      if (n == 0)
      {
         another.html("Attach a video");
      }
      else
      {
         another.html("Attach another video");
      }
   }

   function addVideo()
   {
      var id = "video-" + vid;

      var fakeForm =
         '<div id="' + id + '" class="row">' +
            '<div class="columns r">' +
               '<div class="input-group">' +
                  '<span class="input-group-label"><i class="fi-video"></i></span>' +
                  '<input class="input-group-field" type="text">' +
                  '<div class="input-group-button">' +
                     '<button type="button" class="button r">Attach</button>' +
                  '</div>' +
               '</div>' +
            '</div>' +
            '<div class="small-2 columns r">' +
               '<a href="#">Remove</a>' +
            '</div>' +
         '</div>';

      var n = $('#attachment div').length;

      var another = $('#attach-another');
      if (n == 0)
      {
         if (another.length > 0)
         {
            another.before(fakeForm);
         }
         else
         {
            vidDiv.append(fakeForm);
         }
      }
      else
      {
         $('#attachment div.row:last').after(fakeForm);
      }

      $('#' + id + ' a').click(function() {
         $('#' + id).remove();
         relabelAttachLink();
         return false;
      });

      var vidText = $('#' + id + ' input');

      $('#' + id + ' button').click(function() {
         var button = $(this);
         button.attr('disabled', 'disabled');
         $.ajax({
            url: '/oembed/fetch/',
            type: 'POST',
            data: {
               q : vidText.val()
            },
            dataType: 'json',
            success: function (data, textStatus) {
               $('#' + id + " .r").remove();
               var myDiv = $('#' + id);
               var html =
                  '<div class="columns">' +
                     data.embed +
                     '<p><a href="#"><i class="fi-x"></i> Remove ' +
                        '<i class="fi-arrow-up"></i></a></p>' +
                  '</div>';
               myDiv.prepend(html);
               $('#' + id + ' a').click(function() {
                  myDiv.remove();
                  relabelAttachLink();
                  return false;
               });
            },
            error: function (xhr, textStatus, ex) {
               alert('Oops, an error occurred. ' + xhr.statusText + ' - ' +
                  xhr.responseText);
               button.removeAttr('disabled');
            }
         });
      });

      if (vid == 0)
      {
         $('#video-0').after('<a id="attach-another" href="#">Attach another video</a>');
         $('#attach-another').click(function() {
            addVideo();
            relabelAttachLink();
            return false;
         });
      }
      ++vid;
   }

   initAttachments();

   var topicTitle = $('#id_name');
   var topicSearchButton = $('#search_topics');
   var searchBusy = $('#search-busy-icon');
   topicSearchButton.click(function () {
      var text = $.trim(topicTitle.val());
      if (!text) return;

      $(this).attr('disabled', 'disabled');
      $('#quick-search-results').remove();
      searchBusy.toggle();

      $.ajax({
         url: '/search/ajax/',
         type: 'GET',
         data: {
            q : text,
            models : 'forums.topic'
         },
         traditional: true,
         dataType: 'html',
         success: function (data, textStatus) {
            topicSearchButton.removeAttr('disabled');
            searchBusy.hide();
            searchBusy.after(data);
            $('#hide-search-results').click(function() {
               var results = $('#quick-search-results');
               results.fadeOut(1500, function() { results.remove(); });
            });
         },
         error: function (xhr, textStatus, ex) {
            topicSearchButton.removeAttr('disabled');
            searchBusy.hide();
            alert('Oops, an error occurred. ' + xhr.statusText + ' - ' +
               xhr.responseText);
         }
         });
      return false;
   });
});
