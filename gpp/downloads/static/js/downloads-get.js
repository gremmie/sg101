$(document).ready(function() {
    $('.dl-button').each(function(n) {
        var button = $(this);
        var id = button.attr('id');
        var numeric_id = -1;
        if (id.match(/dl-(\d+)/))
        {
            numeric_id = RegExp.$1;
        }
        button.click(function() {
           button.attr('disabled', 'disabled').val('Getting link, stand by...');
           $.ajax({
               url: '/downloads/request/', 
               type: 'POST',
               data: { id: numeric_id },
               dataType: 'json',
               success: function(result) {
                  var link_id = result.id;
                  var div = $('#link-' + link_id);
                  div.hide();
                  div.html(
                     'Thank you! Your download is now ready. <a href="' + result.url +
                        '">Click here to download</a>.');
                  div.fadeIn(3000);
               },
               error: function (xhr, textStatus, ex) {
                   alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
                      xhr.responseText);
               }
           });
        });
    });
});
