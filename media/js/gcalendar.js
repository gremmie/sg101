$(document).ready(function() {
    $('#id_description').markItUp(mySettings);
    $('#id_start_date').datepicker({constrainInput: true, 
       onClose: function () {
         var end = $('#id_end_date');
         if (this.value > end.val())
         {
            end.val(this.value);
         }
       }
       });
    $('#id_end_date').datepicker({constrainInput: true,
       onClose: function () {
         var start = $('#id_start_date');
         if (this.value < start.val())
         {
            start.val(this.value);
         }
       }
       });
    if ($('#id_all_day:checked').length)
    {
       $('#id_start_time').hide();
       $('#id_end_time').hide();
       $('#id_tz_stuff').hide();
    }
    $('#id_all_day').click(function () {
       $('#id_start_time').toggle();
       $('#id_end_time').toggle();
       $('#id_tz_stuff').toggle();
       });
});
