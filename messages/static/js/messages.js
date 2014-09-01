function tabMasterCheckClick(box, name) {
   var state = $(box).prop('checked');
   $('input[name="' + name + '"]').each(function() {
      this.checked = state;
   });
}

function bulkMsgAction(action) {
   return confirm("Really " + action + " checked messages?");
   return false;
}
