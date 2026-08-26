/* Colour theme switch.
   The stored choice is applied by the inline snippet in each <head>, before
   first paint, so there is no flash. This file only wires the buttons up.
   With no stored choice the page follows the OS via color-scheme: light dark. */
(function () {
  var root = document.documentElement;
  var buttons = document.querySelectorAll("[data-set-theme]");
  var prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

  function current() {
    return root.dataset.theme || (prefersDark.matches ? "dark" : "light");
  }

  function paint() {
    var now = current();
    Array.prototype.forEach.call(buttons, function (button) {
      button.setAttribute("aria-pressed", String(button.dataset.setTheme === now));
    });
  }

  Array.prototype.forEach.call(buttons, function (button) {
    button.addEventListener("click", function () {
      var choice = button.dataset.setTheme;
      root.dataset.theme = choice;
      try { localStorage.setItem("theme", choice); } catch (e) { /* private mode */ }
      paint();
    });
  });

  /* keep the highlight honest if the OS flips and no choice is pinned */
  prefersDark.addEventListener("change", paint);

  paint();
})();
