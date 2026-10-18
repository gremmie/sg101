// The smiley picker: clicking a smiley inserts its code into the active post
// box. Like the old forums' smiley window, it leaves the page usable (no
// overlay, set in its markup) and can be dragged aside by its title.

import { insertAtCursor } from './editor.js';

// Foundation's medium breakpoint. Below it Reveal shows the picker full-screen.
const DRAGGABLE = window.matchMedia('(min-width: 40em)');

// How much of the title must stay on screen across, in pixels.
const KEEP = 100;

export function initSmileys(getTextarea) {
   const modal = document.getElementById('smiley-modal');
   if (!modal) {
      return;
   }
   for (const button of modal.querySelectorAll('button[data-code]')) {
      button.addEventListener('click', () => {
         insertAtCursor(getTextarea(), button.dataset.code, { padded: true });
      });
   }
   makeDraggable(modal, modal.querySelector('.smiley-modal-title'));
}

// Reveal places the modal with top and left, and puts it back in the middle
// when the window is resized.
function makeDraggable(modal, handle) {
   let start = null;

   handle.addEventListener('pointerdown', (event) => {
      // The close button sits on the title; capturing its press would stop
      // the click reaching it.
      if (!DRAGGABLE.matches || event.button !== 0 || event.target.closest('button')) {
         return;
      }
      const box = modal.getBoundingClientRect();
      const title = handle.getBoundingClientRect();
      // The pointer's offset in the modal, and the title's edges relative to
      // the modal's corner, which is what top and left place.
      start = {
         x: event.clientX - box.left,
         y: event.clientY - box.top,
         left: title.left - box.left,
         right: title.right - box.left,
         top: title.top - box.top,
         bottom: title.bottom - box.top,
      };
      handle.setPointerCapture(event.pointerId);
      event.preventDefault();
   });

   handle.addEventListener('pointermove', (event) => {
      if (!start) {
         return;
      }
      const left = clamp(event.clientX - start.x,
                         KEEP - start.right, window.innerWidth - KEEP - start.left);
      const top = clamp(event.clientY - start.y,
                        -start.top, window.innerHeight - start.bottom);
      modal.style.left = `${left}px`;
      modal.style.top = `${top}px`;
   });

   const stop = () => {
      start = null;
   };
   handle.addEventListener('pointerup', stop);
   handle.addEventListener('pointercancel', stop);
}

function clamp(value, low, high) {
   return Math.min(Math.max(value, low), high);
}
