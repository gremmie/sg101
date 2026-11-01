// The upload modal: images from the member's device, listed with thumbnails
// as they are chosen, turned into image codes.
//
// A file input cannot drop one file from its selection, and a second choice
// replaces the first, so the list is kept here: each choice is added to it
// and the input cleared.
//
// Upload sends the list one request at a time, in order, and each code goes
// into the post as its image lands. Closing the modal stops what has not been
// sent; the file in flight finishes, since the server may already have it.

import { postForm, RequestError } from '../core/http.js';
import { insertAtCursor } from './editor.js';
import { hideStatus, showStatus } from './status.js';

const MAX_FILES = 10;
// Sending the file counts against this, and a large photo on a slow connection
// takes minutes. The server is not waiting on it: Cloudflare holds the whole
// upload before passing it on.
const UPLOAD_TIMEOUT_MS = 5 * 60 * 1000;
const UNREADABLE = 'Something went wrong with this image. Please try again.';

// A page never sees a file's path, so a file chosen again is recognised by
// what it can see.
const fileKey = (file) => `${file.name}\n${file.size}\n${file.lastModified}`;

// ['a'] -> 'a'; ['a', 'b', 'c'] -> 'a, b and c'
function listNames(names) {
   return names.length === 1 ? names[0] :
      `${names.slice(0, -1).join(', ')} and ${names.at(-1)}`;
}

export function initUploads(getTextarea) {
   const form = document.getElementById('photo-upload-form');
   if (!form) {
      return () => {};
   }
   const input = form.elements.image_file;
   const choose = document.getElementById('photo-upload-choose');
   const list = document.getElementById('photo-upload-list');
   const submit = document.getElementById('photo-upload-submit');
   const status = document.getElementById('photo-status');
   const idle = submit.value;

   // Each entry: { file, url, item, removeButton, result }. url is the
   // thumbnail's object URL, which holds the file until it is revoked.
   let entries = [];

   // The batch being sent, or null; and whether the modal has been closed and
   // opened again since it began.
   let batch = null;
   let stopped = false;

   function showProgress() {
      const total = batch.entries.filter((e) => entries.includes(e)).length;
      submit.value = `Uploading ${batch.sent} of ${total}\u2026`;
   }

   function remove(entry) {
      URL.revokeObjectURL(entry.url);
      entry.item.remove();
      entries = entries.filter((e) => e !== entry);
      if (batch) {
         showProgress();
      }
   }

   function clear() {
      for (const entry of entries) {
         URL.revokeObjectURL(entry.url);
      }
      entries = [];
      list.replaceChildren();
   }

   function add(file) {
      const url = URL.createObjectURL(file);
      const item = document.createElement('li');
      const thumb = document.createElement('img');
      thumb.className = 'upload-thumb';
      thumb.alt = '';
      // A file the browser cannot draw keeps its place, with a placeholder;
      // the server decides whether it is an image.
      thumb.addEventListener('error', () => {
         const placeholder = document.createElement('span');
         placeholder.className = 'upload-placeholder';
         placeholder.textContent = 'No preview';
         thumb.replaceWith(placeholder);
      });
      thumb.src = url;
      const name = document.createElement('span');
      name.className = 'upload-name';
      name.textContent = file.name;
      const result = document.createElement('span');
      result.className = 'upload-result';
      const detail = document.createElement('div');
      detail.className = 'upload-detail';
      detail.append(name, result);
      const removeButton = document.createElement('button');
      removeButton.type = 'button';
      removeButton.className = 'upload-remove';
      removeButton.setAttribute('aria-label', `Remove ${file.name}`);
      removeButton.innerHTML = '<span aria-hidden="true">&times;</span>';
      item.append(thumb, detail, removeButton);
      list.append(item);

      const entry = { file, url, item, removeButton, result };
      removeButton.addEventListener('click', () => remove(entry));
      entries.push(entry);
   }

   choose.addEventListener('click', () => input.click());

   input.addEventListener('change', () => {
      hideStatus(status);
      const listed = new Set(entries.map((entry) => fileKey(entry.file)));
      const chosen = [];
      const skipped = [];
      for (const file of input.files) {
         if (listed.has(fileKey(file))) {
            skipped.push(file.name);
         } else {
            listed.add(fileKey(file));
            chosen.push(file);
         }
      }
      const room = MAX_FILES - entries.length;
      chosen.slice(0, room).forEach(add);
      input.value = '';

      const messages = [];
      if (skipped.length > 0) {
         messages.push(`${listNames(skipped)} ` +
            `${skipped.length === 1 ? 'is' : 'are'} already in the list.`);
      }
      const left = chosen.length - room;
      if (left > 0) {
         messages.push(`You can upload up to ${MAX_FILES} images at a time; ` +
            `${left} ${left === 1 ? 'was' : 'were'} left out.`);
      }
      if (messages.length > 0) {
         showStatus(status, messages.join(' '), false);
      }
   });

   function setBusy(busy) {
      submit.disabled = busy;
      submit.classList.toggle('disabled', busy);
      choose.disabled = busy;
      choose.classList.toggle('disabled', busy);
      input.disabled = busy;
      if (!busy) {
         submit.value = idle;
      }
   }

   // state is 'sending', 'added' or 'failed'.
   function mark(entry, state, text) {
      entry.result.textContent = text;
      entry.result.className = `upload-result upload-${state}`;
   }

   // Sends one file; its code goes into the textarea the batch began from.
   // Returns whether it was added.
   async function send(entry, textarea) {
      const data = new FormData(form);
      data.set('image_file', entry.file);
      try {
         const response = await postForm(form.action, data,
            { timeoutMs: UPLOAD_TIMEOUT_MS });
         const { url } = await response.json();
         insertAtCursor(textarea, `![image](${url})`, { ownLine: true });
         mark(entry, 'added', '\u2713');
         return true;
      } catch (error) {
         const reason = error instanceof RequestError ? error.message : UNREADABLE;
         mark(entry, 'failed', `\u2717 ${reason}`);
         return false;
      }
   }

   form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (entries.length === 0) {
         showStatus(status, 'Please choose a file to upload.', false);
         return;
      }
      hideStatus(status);
      const textarea = getTextarea();
      batch = { entries: [...entries], sent: 0 };
      stopped = false;
      setBusy(true);
      const added = [];
      for (const entry of batch.entries) {
         // A hidden form has no offsetParent: the modal was closed.
         if (stopped || form.offsetParent === null) {
            break;
         }
         if (!entries.includes(entry)) {
            continue;
         }
         batch.sent += 1;
         showProgress();
         entry.removeButton.disabled = true;
         mark(entry, 'sending', 'Uploading\u2026');
         if (await send(entry, textarea)) {
            added.push(entry);
         } else {
            entry.removeButton.disabled = false;
         }
      }
      const { sent } = batch;
      batch = null;
      added.forEach(remove);
      setBusy(false);
      showStatus(status, `${added.length} of ${sent} added`, added.length === sent);
   });

   // Called as the modal opens: an empty list and no old message.
   return function reset() {
      // Only a closed modal can be opened, so this batch was closed on. What it
      // has in flight is still shown, and it ends when that lands.
      if (batch) {
         stopped = true;
         return;
      }
      clear();
      form.reset();
      hideStatus(status);
   };
}
