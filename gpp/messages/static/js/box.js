function messages_master_click()
{
   var state = document.getElementById('master_select').checked
   for (i = 0; i < document.messages_box_form.length; ++i)
   {
      if (document.messages_box_form.elements[i].type == 'checkbox')
      {
         document.messages_box_form.elements[i].checked = state;
      }
   }
}

function messages_set_master()
{
   var count = 0;
   var numChkBoxes = 0;
   for (i = 0; i < document.messages_box_form.length; ++i)
   {
      if (document.messages_box_form.elements[i].type == 'checkbox' &&
          document.messages_box_form.elements[i].id != 'master_select')
      {
         ++numChkBoxes;
         if (document.messages_box_form.elements[i].checked)
         {
            ++count;
         }
      }
   }
   document.getElementById('master_select').checked = count == numChkBoxes;
}

function messages_count_selected()
{
   var count = 0;
   for (i = 0; i < document.messages_box_form.length; ++i)
   {
      if (document.messages_box_form.elements[i].type == 'checkbox' &&
          document.messages_box_form.elements[i].checked &&
          document.messages_box_form.elements[i].id != 'master_select')
      {
         ++count;
      }
   }
   return count;
}

function messages_confirm_delete()
{
   var count = messages_count_selected();
   if (count == 0)
   {
      alert("No messages selected.");
      return false;
   }
   return confirm('Really delete selected messages?');
}

function messages_confirm_undelete()
{
   var count = messages_count_selected();
   if (count == 0)
   {
      alert("No messages selected.");
      return false;
   }
   return confirm('Really undelete selected messages?');
}
