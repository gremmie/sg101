$(document).ready(function() {

   // allow HTML in title for 1.10
   $.widget("ui.dialog", $.extend({}, $.ui.dialog.prototype, {
       _title: function(title) {
           if (!this.options.title ) {
               title.html("&#160;");
           } else {
               title.html(this.options.title);
           }
       }
   }));

   $tabs = $('#tabs').tabs({
      selected: initialTab,
      select: function(event, ui) {
         $(ui.panel).html('');
      },
      load: function(event, ui) {
         selectedTab = ui;
         if (ui.index == 1 && receiver && !doReply)
         {
            $('#id_receiver').val(receiver);
            receiver = '';
         }
         else if (doReply && ui.index == 1)
         {
            doReply = false;
            var msg = msgCache[$msgDialog.msgId];
            $('#id_receiver').val(msg.sender);
            $('#id_subject').val(msg.re_subject);
            $('#id_message').val(msg.re_content);
            $('#msg_compose_form').append('<input type="hidden" name="reply_to" value="' +
               $msgDialog.msgId + '" />');
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
      height: 'auto',
      maxHeight: false,
      resizable: false,
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

function updateUnreadMsgText(n)
{
   var txt = '';
   if (n == 1) {
      txt = "1 New Message";
   }
   else if (n > 1) {
      txt = n + " New Messages";
   }
   else {
      txt = "Private Messages";
   }
   $('#unread_msg_text').html(txt);
}

function showMsg(link, id) {
   $msgDialog.msgId = id;  // create a msgId attribute on the dialog
   var msg = msgCache[id];

   // mark as read if necessary
   var $link = $(link);

   if (username == msg.receiver && $link.hasClass('unread')) {
      $(link).removeClass('unread');

      // decrement count of unread messages in base template
      if (unreadMsgCount > 0)
      {
         updateUnreadMsgText(--unreadMsgCount);
      }
   }

   var s = '<div style="max-height:450px;overflow:auto">' + msg.content + '</div>';
   $msgDialog.html(s);
   var title = 'PM From ' + msg.sender + ' To ' + msg.receiver + '<br />' + msg.subject;
   $msgDialog.dialog('option', 'title', title);
   $msgDialog.dialog('open');
}

function msgShow(link, id) {
   if (msgCache[id]) {
      showMsg(link, id);
      return;
   }
   $.ajax({
      url: '/messages/message/',
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
      url: '/messages/options-tab/',
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
      url: '/messages/compose-tab/',
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

function tabMasterCheckClick(box, name) {
   var state = $(box).attr('checked');
   $('input[name="' + name + '"]').each(function() {
      this.checked = state;
   });
}

function bulkMsgAction(form, action) {
   if (confirm("Really " + action + " checked messages?")) {
      $.ajax({
         url: '/messages/bulk/',
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
