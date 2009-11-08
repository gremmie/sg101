$(document).ready(function() {
   var postText = $('#id_body');
   var postButton = $('#forums-reply-post');
   postButton.click(function () {
      var text = $.trim(postText.val());
      if (text.length == 0) {
         alert('Please enter some reply text.');
         return false;
      }
      $(this).attr('disabled', 'disabled').val('Posting reply...');
      $.ajax({
         url: '/forums/quick-reply/', 
         type: 'POST',
         data: {
         body : postText.val(),
         topic_id : $('#id_topic_id').val()
         },
         dataType: 'html',
         success: function (data, textStatus) {
            postText.val('');
            $('#forum-topic tr:last').after(data);
            var lastTr = $('#forum-topic tr:last');
            lastTr.hide();
            lastTr.fadeIn(3000);
            postButton.removeAttr('disabled').val('Submit Reply');
         },
         error: function (xhr, textStatus, ex) {
            alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
               xhr.responseText);
            postButton.removeAttr('disabled').val('Submit Reply');
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
   $('#id_body').markItUp(mySettings);
   $('#smileys_dialog').dialog({autoOpen:false});
   var firstTime = true;
   $('#more_smileys').click(function () {
         $('#smileys_dialog').dialog('open');
         var postBox = $('#id_body')[0];
         if (firstTime) {
            $.ajax({
               url: '/smiley/farm/extra/',
               type: 'GET',
               dataType: 'html',
               success: function(data, textStatus) {
                  var img = $('#smiley_busy');
                  img.hide();
                  img.after(data);
                  $('#smileys_dialog .smiley_farm img').click(function() {
                     postBox.value += ' ' + this.alt + ' ';
                     postBox.focus();
                  });
                  firstTime = false;
               },
               error: function (xhr, textStatus, ex) {
                  alert('Oops, an error occurred: ' + xhr.statusText + ' - ' + xhr.responseText);
               }
            });
         }
         return false;
      });
});
