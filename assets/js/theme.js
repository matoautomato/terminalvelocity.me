(function () {
  var root = document.documentElement;
  var button = document.querySelector(".theme-toggle");
  if (!button) return;

  var prefersDark = window.matchMedia("(prefers-color-scheme: dark)");

  button.addEventListener("click", function () {
    var current = root.dataset.theme || (prefersDark.matches ? "dark" : "light");
    var next = current === "dark" ? "light" : "dark";
    root.dataset.theme = next;
    try { localStorage.setItem("theme", next); } catch (e) {}
  });
})();
