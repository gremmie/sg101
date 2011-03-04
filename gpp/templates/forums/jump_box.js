<script type="text/javascript">
//<![CDATA[
$(document).ready(function() {
   var jumpSelect = $('#forum-jumpbox-select')[0];
   $('#forum-jumpbox-button').click(function() {
      var dest = jumpSelect.options[jumpSelect.selectedIndex].value;
      window.location = dest;
   });
});
//]]>
</script>
