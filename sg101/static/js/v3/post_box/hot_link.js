// The hot-link modal: an image address, turned into an image code.

import { imageForm } from './image_form.js';

export function initHotLink(getTextarea) {
   const form = document.getElementById('hot-link-form');
   if (!form) {
      return () => {};
   }
   return imageForm({
      form,
      field: 'url',
      empty: 'Please enter a link to an image.',
      busy: 'Retrieving...',
      submit: document.getElementById('hot-link-form-submit'),
      status: document.getElementById('hot-link-status'),
      getTextarea,
   });
}
