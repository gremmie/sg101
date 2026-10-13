// The hot-link and upload modals work the same way: a form posted to an
// endpoint that answers {error_msg, url}, whose image code is inserted into
// the active post box.

import { postForm } from '../core/http.js';
import { insertAtCursor } from './editor.js';
import { hideStatus, showStatus } from './status.js';

const SUCCESS = 'Success! The image code was added to your post.';

// form: the modal's form. field: the input that must not be empty, and empty
// the message saying so. busy: the submit button's label while posting.
// getTextarea: returns the post box to insert into.
export function imageForm({ form, field, empty, busy, submit, status, getTextarea }) {
   const idle = submit.value;

   form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (!form.elements[field].value) {
         showStatus(status, empty, false);
         return;
      }
      hideStatus(status);
      submit.disabled = true;
      submit.classList.add('disabled');
      submit.value = busy;
      try {
         const response = await postForm(form.action, new FormData(form));
         const { url } = await response.json();
         insertAtCursor(getTextarea(), `![image](${url})`, { ownLine: true });
         showStatus(status, SUCCESS, true);
         form.reset();
      } catch (error) {
         // The field keeps its value, so a mistake can be corrected.
         showStatus(status, error.message, false);
      } finally {
         submit.disabled = false;
         submit.classList.remove('disabled');
         submit.value = idle;
      }
   });

   // Called as the modal opens: a clean form and no old message.
   return function reset() {
      form.reset();
      hideStatus(status);
   };
}
