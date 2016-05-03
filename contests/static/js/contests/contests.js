$(function() {
   var $button = $('#contest-button');
   $button.click(function() {
      var buttonLabel = $button.text();
      $button.attr('disabled', 'disabled').val('Please wait...');

      $.ajax({
         url: '/contests/enter/', 
         type: 'POST',
         data: {
            contest_id : contest_id
         },
         dataType: 'json',
         success: function (data, textStatus) {
            var classname = 'success callout';
            var $p = $('#contest-entry');
            $p.hide();
            $p.addClass(classname);
            $p.html(data.msg);
            $p.fadeIn(3000);
         },
         error: function (xhr, textStatus, ex) {
            alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
               xhr.responseText);
            $button.removeAttr('disabled').text(buttonLabel);
         }
      });
      return false;
   });
});
