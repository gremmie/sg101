// The forum select boxes, the jump box and the list of topics to show: Go
// takes the browser to the chosen option's URL. Each box is marked with
// data-forum-nav and holds one <select> and its Go button.

function initForumNav() {
   for (const box of document.querySelectorAll('[data-forum-nav]')) {
      const select = box.querySelector('select');
      box.querySelector('button').addEventListener('click', () => {
         window.location.assign(select.value);
      });
   }
}

initForumNav();
