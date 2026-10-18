// Text operations on a post box's textarea.

// Textareas the member has been in. One they never focused reports its caret
// at the start, so text inserted into it goes at the end instead.
const focused = new WeakSet();

export function trackCaret(textarea) {
   textarea.addEventListener('focus', () => focused.add(textarea), { once: true });
}

function replaceText(textarea, i, j, text) {
   textarea.value = textarea.value.substring(0, i) + text +
      textarea.value.substring(j);
}

export function wrapSelection(textarea, wrap) {
   const i = textarea.selectionStart;
   const j = textarea.selectionEnd;
   if (wrap.length === 0 || i === j) {
      return;
   }
   const selection = textarea.value.substring(i, j);
   replaceText(textarea, i, j, wrap + selection + wrap);
   textarea.focus();
   textarea.setSelectionRange(i, j + 2 * wrap.length);
}

export function prependLines(textarea, prefix) {
   const i = textarea.selectionStart;
   const j = textarea.selectionEnd;
   const selection = textarea.value.substring(i, j);
   replaceText(textarea, i, j, prefix + selection.replace(/\n/gm, '\n' + prefix));
}

export function insertLink(textarea, url) {
   const i = textarea.selectionStart;
   const j = textarea.selectionEnd;
   const text = i === j ? 'Link' : textarea.value.substring(i, j);
   replaceText(textarea, i, j, `[${text}](${url})`);
   textarea.focus();
}

// Replaces the selection with text and leaves the caret after it. With
// ownLine, newlines are added where needed so the text sits on a line of its
// own; with padded, spaces, so it is a word of its own (a smiley code renders
// only between whitespace). The textarea keeps its selection while a modal
// has the focus, so this works from a modal's button too.
export function insertAtCursor(textarea, text, { ownLine = false, padded = false } = {}) {
   const end = textarea.value.length;
   const placed = focused.has(textarea);
   const i = placed ? textarea.selectionStart : end;
   const j = placed ? textarea.selectionEnd : end;
   const before = textarea.value.substring(0, i);
   const after = textarea.value.substring(j);
   if (ownLine) {
      if (before && !before.endsWith('\n')) {
         text = '\n' + text;
      }
      if (after && !after.startsWith('\n')) {
         text += '\n';
      }
   }
   if (padded) {
      if (before && !/\s$/.test(before)) {
         text = ' ' + text;
      }
      if (after && !/^\s/.test(after)) {
         text += ' ';
      }
   }
   replaceText(textarea, i, j, text);
   textarea.setSelectionRange(i + text.length, i + text.length);
}
