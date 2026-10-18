// The post box: a Markdown textarea with a toolbar. This entry module wires
// every post box on the page.
//
// A page has one set of modals however many post boxes it has, so the post
// box whose modal button was clicked last is the active one, and the modals
// insert into it. Foundation opens and closes the modals through their
// data-open and data-close attributes; nothing here calls jQuery.

import { insertLink, prependLines, trackCaret, wrapSelection } from './editor.js';
import { initHotLink } from './hot_link.js';
import { showPreview } from './preview.js';
import { initSmileys } from './smileys.js';
import { initUploads } from './uploads.js';

let active = null;
const getActive = () => active;

const resetHotLink = initHotLink(getActive);
const resetUploads = initUploads(getActive);
initSmileys(getActive);

const TEXT_BUTTONS = {
   '.editor-bold': (textarea) => wrapSelection(textarea, '**'),
   '.editor-italic': (textarea) => wrapSelection(textarea, '_'),
   '.editor-strike': (textarea) => wrapSelection(textarea, '---'),
   '.editor-quote': (textarea) => prependLines(textarea, '> '),
   '.editor-code': (textarea) => prependLines(textarea, '    '),
   '.editor-bullet': (textarea) => prependLines(textarea, '* '),
   '.editor-number': (textarea) => prependLines(textarea, '1. '),
   '.editor-link': (textarea) => {
      const url = window.prompt('Please enter a URL:', 'https://');
      if (url) {
         insertLink(textarea, url);
      }
   },
};

// Each runs as its modal opens, after the post box is made active.
const MODAL_BUTTONS = {
   '.editor-hot-link': () => resetHotLink(),
   '.editor-upload': () => resetUploads(),
   '.editor-smiley': () => {},
   '.editor-preview': (textarea) => showPreview(textarea),
   '.editor-help': () => {},
};

for (const editor of document.querySelectorAll('.v3-editor')) {
   const textarea = editor.querySelector('textarea');
   trackCaret(textarea);
   // The smiley picker leaves the page usable, so the member can move to
   // another post box while it is open.
   textarea.addEventListener('focus', () => {
      active = textarea;
   });

   for (const [selector, action] of Object.entries(TEXT_BUTTONS)) {
      editor.querySelector(selector)?.addEventListener('click', (event) => {
         event.preventDefault();
         action(textarea);
      });
   }
   for (const [selector, action] of Object.entries(MODAL_BUTTONS)) {
      editor.querySelector(selector)?.addEventListener('click', () => {
         active = textarea;
         action(textarea);
      });
   }
}
