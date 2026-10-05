// TinyMCE finds its plugins, themes and languages relative to its own script,
// which it locates by matching "tiny_mce.js" in a script's src. A hashed name
// such as tiny_mce.048a6a57718e.js does not match, so it falls back to the
// page's directory and every plugin 404s. Telling it the base outright avoids
// the search; this file sits beside the tiny_mce directory, so the base is
// derived from where this script was served rather than from STATIC_URL.
// Must load before tiny_mce.js, which reads this once as it starts.
var tinyMCEPreInit = {
   base: document.currentScript.src.replace(/[^\/]*$/, "") + "tiny_mce",
   suffix: "",
   query: ""
};
