$(document).ready(function() {
    $('#comment-form-post').click(function () {
        $(this).attr('disabled', 'disabled').val('Posting Comment...');
        $.post('/comments/post/', { 
            comment : $('#id_comment').val(), 
            content_type : $('#id_content_type').val(), 
            object_pk : $('#id_object_pk').val() 
            }, 
            function (data, textStatus) {
                $('#id_comment').val(''); 
                $('#comment-list').append(data);
                var lastLi = $('#comment-list > li:last');
                lastLi.hide();
                lastLi.fadeIn(3000);
                $('#comment-form-post').removeAttr('disabled').val('Post Comment');
                var count = $('#comment-count');
                if (count.length) {
                    count.html(parseInt(count.html()) + 1);
                }
            }, 
            'html');
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
                $.post('/comments/flag/', { id : id }, function(response) {
                    alert(response);
                    }, 'text');
            }
        }
        return false;
    });
    $('#id_comment').markItUp(mySettings);
});
