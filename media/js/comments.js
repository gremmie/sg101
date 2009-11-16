$(document).ready(function() {
    var postText = $('#id_comment');
    var postButton = $('#comment-form-post');
    postButton.click(function () {
        var text = $.trim(postText.val());
        if (text.length == 0) {
           alert('Please enter some text.');
           return false;
        }
        postButton.attr('disabled', 'disabled').val('Posting Comment...');
        $.ajax({
            url: '/comments/post/',
            type: 'POST',
            data: {
               comment : text,
               content_type : $('#id_content_type').val(), 
               object_pk : $('#id_object_pk').val() 
            }, 
            dataType: 'html',
            success: function (data, textStatus) {
                postText.val(''); 
                $('#comment-list').append(data);
                var lastLi = $('#comment-list > li:last');
                lastLi.hide();
                lastLi.fadeIn(3000);
                postButton.removeAttr('disabled').val('Post Comment');
                var count = $('#comment-count');
                if (count.length) {
                    count.html(parseInt(count.html()) + 1);
                }
            }, 
            error: function (xhr, textStatus, ex) {
               alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
                  xhr.responseText);
               postButton.removeAttr('disabled').val('Post Comment');
            }
        });
        return false;
    });
    $('a.comment-flag').click(function () {
        var id = this.id;
        if (id.match(/fc-(\d+)/)) {
            id = RegExp.$1;
            if (confirm('Only flag a comment if you feel it is spam, abuse, violates site rules, ' +
                    'or is not appropriate. ' +
                    'A moderator will be notified and will review the comment. ' +
                    'Are you sure you want to flag this comment?')) {
                $.ajax({
                  url: '/comments/flag/',
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
    postText.markItUp(mySettings);

   $('#smileys_dialog').dialog({autoOpen:false});
   var firstTime = true;
   $('#more_smileys').click(function () {
         $('#smileys_dialog').dialog('open');
         var postBox = $('#id_comment')[0];
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
   $('#markdown_help_dialog').dialog({autoOpen: false, width: 720, height: 600});
   var firstTimeMd = true;
   $('#markdown_help').click(function () {
         $('#markdown_help_dialog').dialog('open');
         if (firstTimeMd) {
            $.ajax({
               url: '/core/markdown_help/',
               type: 'GET',
               dataType: 'html',
               success: function(data, textStatus) {
                  var img = $('#markdown_busy');
                  img.hide();
                  img.after(data);
                  firstTimeMd = false;
               },
               error: function (xhr, textStatus, ex) {
                  alert('Oops, an error occurred: ' + xhr.statusText + ' - ' + xhr.responseText);
               }
            });
         }
         return false;
      });
});
