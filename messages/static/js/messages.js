function tabMasterCheckClick(box, name) {
   var state = $(box).prop('checked');
   $('input[name="' + name + '"]').each(function() {
      this.checked = state;
   });
}

function bulkMsgAction(action) {
   var total = $('input[name="pm_ids"]:checked').length;
   if (total <= 0) {
      alert('Please check some messages first.');
      return false;
   }
   return confirm("Really " + action + " checked messages?");
   return false;
}
