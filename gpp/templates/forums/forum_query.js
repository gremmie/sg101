<script type="text/javascript">
//<![CDATA[
   $(document).ready(function() {
      var navSelect = $('#forum-query-select')[0];
      $('#forum-query-button').click(function() {
         var dest = navSelect.options[navSelect.selectedIndex].value;
         window.location = dest;
      });
   });
//]]>
</script>
