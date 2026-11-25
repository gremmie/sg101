// Master checkboxes, and the checks a form makes before it submits them.
//
// A box marked data-check-all ticks or unticks every data-check-item box in
// its form, and unticking one of those unticks the master. A form may also
// carry data-none-checked, a warning shown instead of submitting when no box
// is ticked, and data-confirm, a question asked before it submits. In such a
// form, a submit button may carry its own data-confirm, asked only when that
// button is used.

function initCheckAll() {
   for (const master of document.querySelectorAll('[data-check-all]')) {
      const items = master.form.querySelectorAll('[data-check-item]');
      master.addEventListener('change', () => {
         for (const item of items) {
            item.checked = master.checked;
         }
      });
      for (const item of items) {
         item.addEventListener('change', () => {
            if (!item.checked) {
               master.checked = false;
            }
         });
      }
   }
}

function initFormChecks() {
   for (const form of document.querySelectorAll('form[data-none-checked], form[data-confirm]')) {
      form.addEventListener('submit', (event) => {
         const warning = form.dataset.noneChecked;
         if (warning && !form.querySelector('[data-check-item]:checked')) {
            window.alert(warning);
            event.preventDefault();
            return;
         }
         const question = event.submitter?.dataset.confirm ?? form.dataset.confirm;
         if (question && !window.confirm(question)) {
            event.preventDefault();
         }
      });
   }
}

initCheckAll();
initFormChecks();
