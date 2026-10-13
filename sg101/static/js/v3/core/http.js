// The one way the site's modules talk to the server.
//
// Every request carries Django's CSRF token and the X-Requested-With header
// core.functions.is_ajax checks, gives up after a timeout, and fails with a
// RequestError whose message can be shown to the member as it is.

const CSRF_COOKIE = 'csrftoken';

// Longer than this, a text body is a page rather than a sentence.
const MAX_TEXT_MESSAGE = 200;

export class RequestError extends Error {
   constructor(message, status) {
      super(message);
      this.name = 'RequestError';
      this.status = status;
   }
}

function cookie(name) {
   for (const pair of document.cookie.split(';')) {
      const [key, ...value] = pair.trim().split('=');
      if (key === name) {
         return decodeURIComponent(value.join('='));
      }
   }
   return '';
}

// The member's message for a failed response: the JSON body's error_msg, a
// short plain-text body, the status text, or failing all those a fixed
// sentence. An HTML error page, such as a proxy's, is never shown as markup.
async function errorMessage(response) {
   let body = '';
   try {
      body = await response.text();
   } catch (error) {
      // the body could not be read; fall through to the status
   }
   const type = response.headers.get('Content-Type') || '';
   if (type.includes('application/json')) {
      try {
         const message = JSON.parse(body).error_msg;
         if (message) {
            return message;
         }
      } catch (error) {
         // not JSON after all
      }
   } else {
      const text = body.trim();
      if (text && text.length < MAX_TEXT_MESSAGE && !text.includes('<')) {
         return text;
      }
   }
   if (response.statusText) {
      return response.statusText;
   }
   return `Something went wrong (status ${response.status}).`;
}

async function request(url, options, timeoutMs) {
   const controller = new AbortController();
   const timer = setTimeout(() => controller.abort(), timeoutMs);
   let response;
   try {
      response = await fetch(url, {
         ...options,
         credentials: 'same-origin',
         signal: controller.signal,
         headers: {
            'X-CSRFToken': cookie(CSRF_COOKIE),
            'X-Requested-With': 'XMLHttpRequest',
         },
      });
   } catch (error) {
      if (error.name === 'AbortError') {
         throw new RequestError('The server took too long to answer. Please try again.', 0);
      }
      throw new RequestError('Could not reach the server. Please check your connection and try again.', 0);
   } finally {
      clearTimeout(timer);
   }
   if (!response.ok) {
      throw new RequestError(await errorMessage(response), response.status);
   }
   return response;
}

// POSTs formData to url and returns the Response, or throws RequestError.
export function postForm(url, formData, { timeoutMs = 30000 } = {}) {
   return request(url, { method: 'POST', body: formData }, timeoutMs);
}
