$(document).ready(function() {
   $tabs = $('#tabs').tabs({
      selected: initialTab,
      select: function(event, ui) {
         $(ui.panel).html('');
      },
      load: function(event, ui) {
         selectedTab = ui;
         if (doReply && ui.index == 1)
         {
            doReply = false;
            var msg = msgCache[$msgDialog.msgId];
            $('#id_receiver').val(msg.sender);
            $('#id_subject').val(msg.re_subject);
            $('#id_message').val(msg.re_content);
         }
      },
      ajaxOptions: {
         error: function(xhr, status, index, anchor) {
            $(anchor.hash).html(
               "Oops, we couldn't load this tab. We'll try to fix this as soon as possible.");
         }
      }
   });
   $msgDialog = $('#msgDialog').dialog({
      autoOpen: false,
      width: 460,
      buttons: [
         { 
            text: "Reply", 
            click: function() { 
               doReply = true;
               $(this).dialog('close'); 
               $tabs.tabs("select", 1);
            } 
         },
         { 
            text: "Close",
            click: function() { 
               $(this).dialog('close'); 
            } 
         }
      ]
   });
});

var $tabs = 0;
var $msgDialog = 0;
var msgCache = {};
var doReply = false;
var selectedTab = 0;

function showMsg(link, id) {
   $msgDialog.msgId = id;  // create a msgId attribute on the dialog
   var msg = msgCache[id];

   // mark as read if necessary
   if (username == msg.receiver) {
      $(link).removeClass('unread');
   }

   $msgDialog.html(msg.content);
   var title = 'PM From ' + msg.sender + ' To ' + msg.receiver + '<br /> ' + msg.subject;
   $msgDialog.dialog('option', 'title', title);
   $msgDialog.dialog('open');
}

function msgShow(link, id) {
   if (msgCache[id]) {
      showMsg(link, id);
      return;
   }
   $.ajax({
      url: '/messages/beta/message/',
      type: 'POST',
      data: {
         msg_id : id
      },
      dataType: 'json',
      success: function (data, textStatus) {
         msgCache[id] = data;
         showMsg(link, id);
      },
      error: function (xhr, textStatus, ex) {
         alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
            xhr.responseText);
      }
   });
}

function submitOptions(form) {
   $.ajax({
      url: '/messages/beta/options-tab/',
      type: 'POST',
      data: $(form).serialize(),
      dataType: 'html',
      success: function (data, textStatus) {
         $(selectedTab.panel).html(data);
      },
      error: function (xhr, textStatus, ex) {
         alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
            xhr.responseText);
      }
   });
   return false;
}

function messageSubmit(form) {
   $.ajax({
      url: '/messages/beta/compose-tab/',
      type: 'POST',
      data: $(form).serialize(),
      dataType: 'html',
      success: function (data, textStatus) {
         $('#ui-tabs-1').html(data);
      },
      error: function (xhr, textStatus, ex) {
         alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
            xhr.responseText);
      }
   });
   return false;
}

function tabMasterCheckClick(box, name) {
   var state = $(box).attr('checked');
   $('input[name="' + name + '"]').each(function() {
      this.checked = state;
   });
}

function bulkMsgAction(form, action) {
   if (confirm("Really " + action + " checked messages?")) {
      $.ajax({
         url: '/messages/beta/bulk/',
         type: 'POST',
         data: $(form).serialize(),
         dataType: 'text',
         success: function (data, textStatus) {
            $tabs.tabs("load", selectedTab.index);
         },
         error: function (xhr, textStatus, ex) {
            alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
               xhr.responseText);
         }
      });
   }
   return false;
}

function ajaxPageFetch(link) {
   $.ajax({
      url: link.href,
      type: 'GET',
      dataType: 'html',
      success: function (data, textStatus) {
         $(selectedTab.panel).html(data);
      },
      error: function (xhr, textStatus, ex) {
         alert('Oops, an error occurred. ' + xhr.statusText + ' - ' + 
            xhr.responseText);
      }
   });
   return false;
}
