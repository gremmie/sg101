
$(document).ready(function() {
    $('#id_profile_text').markItUp(mySettings);
    $('#id_signature').markItUp(mySettings);
    $('#id_birthday').datepicker({changeMonth: true, 
       changeYear: true,
       dateFormat: 'yy-mm-dd',
       defaultDate: '-30y',
       minDate: new Date(1909, 0, 1),
       maxDate: new Date(),
       yearRange: '-100:+0'});
});
