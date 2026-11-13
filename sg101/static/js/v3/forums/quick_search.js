// The new topic's Quick Search: the subject sent to the topic search, and the
// topics it matches shown under the subject, so a member can see whether
// their question has been asked before they ask it.

import { get } from '../core/http.js';
import { hideStatus, showStatus } from '../post_box/status.js';

const SEARCH_URL = '/search/topics/';
const EMPTY = 'Please enter a subject to search for.';
const BUSY = 'Searching…';

function initQuickSearch() {
   const button = document.getElementById('quick-search');
   if (!button) {
      return;
   }
   const place = button.closest('[data-quick-search]');
   const subject = place.querySelector('input[name="name"]');
   // Only the words change while searching; the icon stays.
   const words = button.querySelector('span');
   const label = words.textContent;
   const status = document.createElement('div');
   status.className = 'callout hidden';
   place.append(status);

   const removeResults = () => place.querySelector('#quick-search-results')?.remove();

   button.addEventListener('click', async () => {
      removeResults();
      const text = subject.value.trim();
      if (!text) {
         showStatus(status, EMPTY, false);
         return;
      }
      hideStatus(status);
      button.disabled = true;
      words.textContent = BUSY;
      try {
         const response = await get(`${SEARCH_URL}?${new URLSearchParams({ q: text })}`);
         place.insertAdjacentHTML('beforeend', await response.text());
      } catch (error) {
         showStatus(status, error.message, false);
      } finally {
         button.disabled = false;
         words.textContent = label;
      }
   });

   place.addEventListener('click', (event) => {
      if (event.target.closest('#hide-search-results')) {
         removeResults();
      }
   });
}

initQuickSearch();
