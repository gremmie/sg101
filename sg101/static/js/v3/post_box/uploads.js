// The upload modal: one image from the member's device, turned into an image
// code.

import { imageForm } from './image_form.js';

export function initUploads(getTextarea) {
   const form = document.getElementById('photo-upload-form');
   if (!form) {
      return () => {};
   }
   return imageForm({
      form,
      field: 'image_file',
      empty: 'Please choose a file to upload.',
      busy: 'Uploading...',
      submit: document.getElementById('photo-upload-submit'),
      status: document.getElementById('photo-status'),
      getTextarea,
   });
}
