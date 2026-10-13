// The preview modal: the post box's text rendered by the server, as it will
// appear when posted.

import { postForm } from '../core/http.js';

const PREVIEW_URL = '/comments/markdown/v3/';

export async function showPreview(textarea) {
   const panel = document.getElementById('editor-preview-panel');
   if (!panel) {
      return;
   }
   panel.textContent = '';
   panel.scrollTop = 0;

   const data = new FormData();
   data.append('data', textarea.value);
   try {
      const response = await postForm(PREVIEW_URL, data);
      // The server's own rendering, cleaned as a post's would be.
      panel.innerHTML = await response.text();
   } catch (error) {
      const message = document.createElement('div');
      message.className = 'alert callout';
      message.textContent = error.message;
      panel.replaceChildren(message);
   }
}
