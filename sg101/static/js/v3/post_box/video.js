// The video modal, forums only: a video's address, turned into an entry in
// the attachment list of the active post box's form. Each entry carries a
// hidden attachment input, so the form sends it as it is.

import { postForm } from '../core/http.js';
import { hideStatus, showStatus } from './status.js';

const EMPTY = 'Please enter a link to a video.';
const BUSY = 'Retrieving...';

// The list the active post box's form keeps its attachments in.
function attachmentList(textarea) {
   return textarea.form.querySelector('[data-attachments]');
}

export function initVideo(getTextarea) {
   const form = document.getElementById('video-form');
   if (!form) {
      return () => {};
   }
   const modal = document.getElementById('video-modal');
   const submit = document.getElementById('video-form-submit');
   const status = document.getElementById('video-status');
   const entryTemplate = document.getElementById('attachment-entry');
   const idle = submit.value;

   form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!form.elements.q.value) {
         showStatus(status, EMPTY, false);
         return;
      }
      hideStatus(status);
      submit.disabled = true;
      submit.classList.add('disabled');
      submit.value = BUSY;
      try {
         const response = await postForm(form.action, new FormData(form));
         const { id, embed } = await response.json();
         const entry = entryTemplate.content.cloneNode(true);
         entry.querySelector('.forum-attachment').innerHTML = embed;
         entry.querySelector('input[name="attachment"]').value = id;
         attachmentList(getTextarea()).append(entry);
         // Foundation closes the modal on its own close button.
         modal.querySelector('[data-close]').click();
      } catch (error) {
         // The field keeps its value, so a mistake can be corrected.
         showStatus(status, error.message, false);
      } finally {
         submit.disabled = false;
         submit.classList.remove('disabled');
         submit.value = idle;
      }
   });

   // Saved attachments arrive in the page, so Remove is handled for every
   // list rather than for each entry as it is made.
   document.addEventListener('click', (event) => {
      const remove = event.target.closest('[data-attachments] .attachment-remove');
      remove?.closest('.forum-attachment-entry').remove();
   });

   // Called as the modal opens: a clean form and no old message.
   return function reset() {
      form.reset();
      hideStatus(status);
   };
}
