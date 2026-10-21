// Category filtering for the advocacy list.
//
// The old site had a separate page per category (/advocacy/category/SEPAW).
// Those URLs now redirect to /advocacy/?category=SEPAW, so the filter reads
// the query string and hides the posts that do not match.
(function () {
  var list = document.getElementById("posts");
  if (!list) return;

  var params = new URLSearchParams(window.location.search);
  var wanted = params.get("category");
  if (!wanted) return;

  var cards = Array.prototype.slice.call(list.querySelectorAll(".card"));
  cards.forEach(function (card) {
    var cats = (card.getAttribute("data-categories") || "").split("|");
    card.hidden = cats.indexOf(wanted) === -1;
  });

  // Mark the matching chip as active.
  var chips = document.querySelectorAll(".filter-chip");
  Array.prototype.forEach.call(chips, function (chip) {
    var label = chip.textContent.trim();
    chip.classList.toggle("is-active", label === wanted);
  });
})();
