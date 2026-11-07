// The topic page: quick reply, and the post tools that act in place, flag and
// delete. What the server says comes back in a callout, never an alert().
//
// The tools are handled by one listener on the posts' container, so a post
// added by quick reply has working tools without anything more to wire.

import { postForm } from '../core/http.js';
import { hideStatus, showStatus } from '../post_box/status.js';

const QUICK_REPLY_URL = '/forums/quick-reply/';
const FLAG_URL = '/forums/flag-post/';
const DELETE_URL = '/forums/delete-post/';

const FLAG_QUESTION = 'Only flag a post if you feel it is spam, abuse, ' +
   'violates site rules, or is not appropriate. A moderator will be ' +
   'notified and will review the post. Are you sure you want to flag this ' +
   'post?';
const DELETE_QUESTION = 'Are you sure you want to delete this post?';
const DELETE_TOPIC_QUESTION = 'Are you sure you want to delete this topic?\n' +
   'WARNING: all posts will be lost.';

const FADE_MS = 1500;

const container = document.getElementById('forum-topic-post-container');

// A hidden callout for messages, made the first time place needs one.
function statusCallout(place) {
   let callout = place.querySelector(':scope > .topic-status');
   if (!callout) {
      callout = document.createElement('div');
      callout.className = 'topic-status callout hidden';
      place.append(callout);
   }
   return callout;
}

function initQuickReply() {
   const button = document.getElementById('forums-reply-post');
   if (!button) {
      return;
   }
   const form = button.form;
   const textarea = form.elements.body;
   const label = button.value;
   const status = document.createElement('div');
   status.className = 'callout hidden';
   button.before(status);

   form.addEventListener('submit', async (event) => {
      event.preventDefault();
      button.disabled = true;
      button.value = 'Posting reply…';
      try {
         const response = await postForm(QUICK_REPLY_URL, new FormData(form));
         container.insertAdjacentHTML('beforeend', await response.text());
         textarea.value = '';
         hideStatus(status);
      } catch (error) {
         // The text stays in the box, to try again.
         showStatus(status, error.message, false);
      } finally {
         button.disabled = false;
         button.value = label;
      }
   });
}

// Asks, then sends the post's id to url. Returns the post's element if the
// server agreed, null otherwise; either way the post shows what it said.
async function postTool(button, url, question) {
   if (!window.confirm(question)) {
      return null;
   }
   const id = button.dataset.postId;
   const post = document.getElementById(`post-${id}`);
   // :scope, as the page's own content column is a .medium-9 too.
   const status = statusCallout(post.querySelector(':scope > .medium-9 .card-section'));
   const data = new FormData();
   data.append('id', id);
   try {
      const response = await postForm(url, data);
      showStatus(status, await response.text(), true);
      return post;
   } catch (error) {
      showStatus(status, error.message, false);
      return null;
   }
}

function initPostTools() {
   container?.addEventListener('click', async (event) => {
      const flag = event.target.closest('button.post-flag');
      if (flag) {
         await postTool(flag, FLAG_URL, FLAG_QUESTION);
         return;
      }
      const remove = event.target.closest('button.post-delete');
      if (remove) {
         const post = await postTool(remove, DELETE_URL, DELETE_QUESTION);
         if (post) {
            await post.animate([{ opacity: 1 }, { opacity: 0 }], FADE_MS).finished;
            post.remove();
         }
      }
   });
}

function initDeleteTopic() {
   const button = document.getElementById('forum-mod-del-topic');
   button?.form.addEventListener('submit', (event) => {
      if (!window.confirm(DELETE_TOPIC_QUESTION)) {
         event.preventDefault();
      }
   });
}

initQuickReply();
initPostTools();
initDeleteTopic();
