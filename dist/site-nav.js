// Native disclosures keep the navigation usable without JavaScript.
(() => {
  const nav = document.querySelector(".siteNav");
  for (const group of nav.querySelectorAll(".navGroup")) {
    document.addEventListener("click", event => {
      if (!group.contains(event.target)) group.open = false;
    });
    group.addEventListener("focusout", event => {
      if (!group.contains(event.relatedTarget)) group.open = false;
    });
    group.addEventListener("keydown", event => {
      if (event.key === "Escape" && group.open) {
        group.open = false;
        group.querySelector("summary").focus();
      }
    });
  }
})();
