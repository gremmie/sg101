function editorReplaceText(textArea, i, j, newText) {
   textArea.value = textArea.value.substring(0, i) + newText +
      textArea.value.substring(j);
}

function editorWrapSelection(textArea, wrapText) {
   if (wrapText.length == 0) return;
   var i = textArea.selectionStart;
   var j = textArea.selectionEnd;
   if (i == j) return;
   var selection = textArea.value.substring(i, j);
   var newText = wrapText + selection + wrapText;
   editorReplaceText(textArea, i, j, newText);
   textArea.focus();
   textArea.setSelectionRange(i, j + 2 * wrapText.length);
}

function editorPrependLines(textArea, s) {
   if (s.length == 0) return;
   var i = textArea.selectionStart;
   var j = textArea.selectionEnd;
   var newText = s;
   var selection = textArea.value.substring(i, j);
   newText += selection.replace(/\n/gm, '\n' + s);
   editorReplaceText(textArea, i, j, newText);
}

function editorLink(textArea) {
   var i = textArea.selectionStart;
   var j = textArea.selectionEnd;
   var url = window.prompt("Please enter a URL:", "http://");
   if (!url) return;
   var link;
   if (i == j) {
      link = '[Link](' + url + ')';
   } else {
      var selection = textArea.value.substring(i, j);
      link = '[' + selection + '](' + url + ')';
   }
   editorReplaceText(textArea, i, j, link);
   textArea.focus();
}

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

   var editorPanel = $('#editor-panel textarea');
   var previewPanel = $('#preview-panel');
   previewPanel.css('height', editorPanel.css('height'));
   var observer = new MutationObserver(function(mutations) {
      if (previewPanel.is(':visible')) {
         alert(editorPanel[0].value);
         $.ajax({
            url: '/comments/markdown/v3/',
            method: 'POST',
            data: {'data': editorPanel[0].value},
            dataType: 'html',
            success: function(data, textStatus) {
               alert(data);
               previewPanel.html(data);
            },
            error: function (xhr, textStatus, ex) {
               alert('Oops, an error occurred: ' + xhr.statusText + ' - ' +
                     xhr.responseText);
            }
         });
      }
   });
   var target = document.getElementById('preview-panel');
   observer.observe(target, {attributes: true});

   // Editor stuff
   $('.v3-editor').each(function (index) {
      var $this = $(this);
      var textArea = $this.find('textarea')[0];
      $this.find('.editor-bold').click(function () {
         editorWrapSelection(textArea, '**');
         return false;
      });
      $this.find('.editor-italic').click(function () {
         editorWrapSelection(textArea, '_');
         return false;
      });
      $this.find('.editor-strike').click(function () {
         editorWrapSelection(textArea, '---');
         return false;
      });
      $this.find('.editor-link').click(function () {
         editorLink(textArea);
         return false;
      });
      $this.find('.editor-quote').click(function () {
         editorPrependLines(textArea, '> ');
         return false;
      });
      $this.find('.editor-code').click(function () {
         editorPrependLines(textArea, '    ');
         return false;
      });
      $this.find('.editor-bullet').click(function () {
         editorPrependLines(textArea, '* ');
         return false;
      });
      $this.find('.editor-number').click(function () {
         editorPrependLines(textArea, '1. ');
         return false;
      });
   });
});
