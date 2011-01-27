$(document).ready(function() {
   var master = $('#forums-master-topic');
   var topics = $('.forums-topic_check');
   master.click(function() {
      var state = this.checked;
      topics.each(function() {
         this.checked = state;
      });
   });
   topics.click(function() {
      if (master[0].checked && !this.checked) {
         master[0].checked = false;
      }
   });
});
