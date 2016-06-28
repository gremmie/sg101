$(document).ready(function() {
    $('#id_start_date').datepicker({constrainInput: true, 
       dateFormat: 'mm/dd/yy',
       onClose: function () {
         var end = $('#id_end_date');
         if (this.value > end.val())
         {
            end.val(this.value);
         }
       }
       });
    $('#id_end_date').datepicker({constrainInput: true,
       dateFormat: 'mm/dd/yy',
       onClose: function () {
         var start = $('#id_start_date');
         if (this.value < start.val())
         {
            start.val(this.value);
         }
       }
       });
    if ($('#id_all_day:checked').length) {
       $('.all-day-hide').hide();
    }
    $('#id_all_day').click(function () {
       $('.all-day-hide').toggle();
    });
});
