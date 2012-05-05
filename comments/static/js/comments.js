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
                $('#comment-container').append(data);
                var newDiv = $('#comment-container > div:last');
                newDiv.hide();
                var num = $('.comment-list', newDiv);
                num.html($('#comment-container > div').size() + ".");
                newDiv.fadeIn(3000);
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

   $('.comment-text img').fadeIn('fast', function() {
         var pic = $(this);
         if (pic.width() > 720) {
            pic.css('width', '720px');
         }
   });
});
