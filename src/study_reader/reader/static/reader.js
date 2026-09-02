const tableOfContents = document.querySelector(".toc-details");
const desktopReader = window.matchMedia("(min-width: 768px)");

function synchronizeTableOfContents(event) {
  tableOfContents.open = event.matches;
}

synchronizeTableOfContents(desktopReader);
desktopReader.addEventListener("change", synchronizeTableOfContents);
