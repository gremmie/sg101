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
   var url = window.prompt("Please enter a URL:", "https://");
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
   var $postBox;
   var previewPanel = $('#editor-preview-panel');

   $('#preview-modal').on('open.zf.reveal', function() {
      previewPanel.html('');
      previewPanel.scrollTop(0);
      $.ajax({
         url: '/comments/markdown/v3/',
         method: 'POST',
         data: {'data': $postBox.val()},
         dataType: 'html',
         success: function(data, textStatus) {
            previewPanel.html(data);
         },
         error: function (xhr, textStatus, ex) {
            alert('Oops, an error occurred: ' + xhr.statusText + ' - ' +
                  xhr.responseText);
         }
      });
   });

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
      $this.find('.editor-hot-link').click(function () {
         $postBox = $(textArea);
      });
      $this.find('.editor-upload').click(function () {
         $postBox = $(textArea);
      });
      $this.find('.editor-preview').click(function () {
         $postBox = $(textArea);
      });
   });

   var $hotLinkForm = $('#hot-link-form');
   if ($hotLinkForm.length) {
      var $hotLinkFormSubmit = $('#hot-link-form-submit');
      var $hotLinkStatus = $('#hot-link-status');

      $('#hot-link-modal').on('open.zf.reveal', function() {
         $hotLinkForm.clearForm();
      });
      $('#hot-link-modal').on('closed.zf.reveal', function() {
         $hotLinkStatus.hide();
      });

      $hotLinkForm.ajaxForm({
         dataType: 'json',
         beforeSubmit: function(arr, $form, options) {
            var url = null;
            $.each(arr, function(index, val) {
               if (val.name == 'url') {
                  url = val.value;
               }
            });
            if (!url) {
               $hotLinkStatus.removeClass('success').addClass('alert');
               $hotLinkStatus.html("Please enter a link to an image.");
               $hotLinkStatus.fadeIn(700);
               return false;
            } else {
               $hotLinkStatus.hide();
            }
            $hotLinkFormSubmit.attr('disabled', 'disabled').val('Retrieving...');
            $hotLinkFormSubmit.addClass('disabled');
            return true;
         },
         success: function(resp, statusText, xhr, $form) {
            $postBox.val($postBox.val() + '\n![image](' + resp.url + ')');
            $hotLinkStatus.removeClass('alert').addClass('success');
            $hotLinkStatus.html("Success! The image code was added to your post.");
            $hotLinkStatus.fadeIn(700);
            $hotLinkForm.clearForm();
         },
         complete: function(xhr) {
            $hotLinkFormSubmit.removeAttr('disabled').val('Hot Link');
            $hotLinkFormSubmit.removeClass('disabled');
         },
         error: function(xhr, textStatus, ex) {
            $hotLinkStatus.removeClass('success').addClass('alert');
            var message = ex;
            try {
               message = $.parseJSON(xhr.responseText).error_msg || ex;
            } catch (e) {
               // not JSON, e.g. a proxy's error page; the status text will do
            }
            $hotLinkStatus.text(message);
            $hotLinkStatus.fadeIn(700);
         }
      });
   }
   var $photoForm = $('#photo-upload-form');
   if ($photoForm.length) {
      var $photoUploadSubmit = $('#photo-upload-submit');
      var $photoStatus = $('#photo-status');

      $('#upload-modal').on('open.zf.reveal', function() {
         $photoForm.clearForm();
      });
      $('#upload-modal').on('closed.zf.reveal', function() {
         $photoStatus.hide();
      });

      $photoForm.ajaxForm({
         dataType: 'json',
         beforeSubmit: function(arr, $form, options) {
            var fileObj = null;
            $.each(arr, function(index, val) {
               if (val.name == 'image_file') {
                  fileObj = val.value;
               }
            });
            if (!fileObj) {
               $photoStatus.removeClass('success').addClass('alert');
               $photoStatus.html("Please choose a file to upload.");
               $photoStatus.fadeIn(700);
               return false;
            } else {
               $photoStatus.hide();
            }
            $photoUploadSubmit.attr('disabled', 'disabled').val('Uploading...');
            $photoUploadSubmit.addClass('disabled');
            return true;
         },
         success: function(resp, statusText, xhr, $form) {
            $postBox.val($postBox.val() + '\n![image](' + resp.url + ')');
            $photoStatus.removeClass('alert').addClass('success');
            $photoStatus.html("Success! The image code was added to your post.");
            $photoStatus.fadeIn(700);
            $photoStatus.clearForm();
         },
         complete: function(xhr) {
            $photoUploadSubmit.removeAttr('disabled').val('Upload photo');
            $photoUploadSubmit.removeClass('disabled');
         },
         error: function(xhr, textStatus, ex) {
            $photoStatus.removeClass('success').addClass('alert');
            var resp = $.parseJSON(xhr.responseText);
            $photoStatus.html("Error: " + ex + ' - ' + resp.error_msg);
            $photoStatus.fadeIn(700);
         }
      });
   }
});
