$(document).ready(function() {
   $.get('/accounts/register/code/', function(data) {
      $('#reg-code-block').text(data.code);
   });
});
