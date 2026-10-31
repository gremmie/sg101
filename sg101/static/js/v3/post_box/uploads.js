// The upload modal: images from the member's device, listed with thumbnails
// as they are chosen, turned into image codes.
//
// A file input cannot drop one file from its selection, and a second choice
// replaces the first, so the list is kept here: each choice is added to it
// and the input cleared.

import { postForm } from '../core/http.js';
import { insertAtCursor } from './editor.js';
import { hideStatus, showStatus } from './status.js';

const MAX_FILES = 10;
const SUCCESS = 'Success! The image code was added to your post.';

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
   const list = document.getElementById('photo-upload-list');
   const submit = document.getElementById('photo-upload-submit');
   const status = document.getElementById('photo-status');
   const idle = submit.value;

   // Each entry: { file, url, item }. url is the thumbnail's object URL, which
   // holds the file until it is revoked.
   let entries = [];

   function remove(entry) {
      URL.revokeObjectURL(entry.url);
      entry.item.remove();
      entries = entries.filter((e) => e !== entry);
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
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'upload-remove';
      button.setAttribute('aria-label', `Remove ${file.name}`);
      button.innerHTML = '<span aria-hidden="true">&times;</span>';
      item.append(thumb, name, button);
      list.append(item);

      const entry = { file, url, item };
      button.addEventListener('click', () => remove(entry));
      entries.push(entry);
   }

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

   // For now Upload sends the first file in the list.
   form.addEventListener('submit', async (event) => {
      event.preventDefault();
      if (entries.length === 0) {
         showStatus(status, 'Please choose a file to upload.', false);
         return;
      }
      hideStatus(status);
      submit.disabled = true;
      submit.classList.add('disabled');
      submit.value = 'Uploading...';
      try {
         const data = new FormData(form);
         data.set('image_file', entries[0].file);
         const response = await postForm(form.action, data);
         const { url } = await response.json();
         insertAtCursor(getTextarea(), `![image](${url})`, { ownLine: true });
         showStatus(status, SUCCESS, true);
         clear();
      } catch (error) {
         // The list keeps its files, so a mistake can be corrected.
         showStatus(status, error.message, false);
      } finally {
         submit.disabled = false;
         submit.classList.remove('disabled');
         submit.value = idle;
      }
   });

   // Called as the modal opens: an empty list and no old message.
   return function reset() {
      clear();
      form.reset();
      hideStatus(status);
   };
}
