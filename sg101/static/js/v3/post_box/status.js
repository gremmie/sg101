// A modal's status callout: hidden until there is something to say.

export function showStatus(callout, message, succeeded) {
   callout.textContent = message;
   callout.classList.toggle('success', succeeded);
   callout.classList.toggle('alert', !succeeded);
   callout.classList.remove('hidden');
}

export function hideStatus(callout) {
   callout.classList.add('hidden');
}
