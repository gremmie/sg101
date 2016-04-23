$(function() {
   $(".sg101-autocomplete").each(function(index) {
      var $this = $(this);
      var cache = {};
      var cacheSize = 0;
      var url = $this.data('autocompleteUrl');

      $this.autocomplete({
         delay: 400,
         minLength: 1,
         source: function(request, response) {
            if (cache[request.term]) {
              response(cache[request.term]);
              return;
            }
            $.ajax({
               url: url,
               type: "GET",
               data: {
                  q: request.term,
                  limit: 15
               },
               dataType: "json",
               success: function(data, textStatus) {
                  if (cacheSize >= 128) {
                    cache = {};
                    cacheSize = 0;
                  }
                  cache[request.term] = data;
                  ++cacheSize;
                  response(data);
               },
               error: function(xhr, textStatus, ex) {
                  alert('Oops, an error occurred. ' + xhr.statusText + ' - ' +
                   xhr.responseText);
               }
            });
         }
      });
   });
});
