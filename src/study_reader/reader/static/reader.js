import {
  DEFAULT_SETTINGS,
  calculateBookProgress,
  calculateChapterProgress,
  normalizeSettings,
  resolveReadingTarget,
} from "./reader-state.js";

const SETTINGS_KEY = "study-reader:v1:appearance";
const body = document.body;
const bookId = body.dataset.bookId;
const chapterId = body.dataset.chapterId;
const bookStateKey = `study-reader:v1:book:${bookId}`;
const chapterLinks = [
  ...document.querySelectorAll(".toc-domain a[data-chapter-id]"),
];
const chapterIds = chapterLinks.map((link) => link.dataset.chapterId);
const article = document.querySelector(".chapter-prose");
const readableBlocks = [...article.querySelectorAll(":scope > [id]")].filter(
  (block) => getComputedStyle(block).display !== "none",
);
const blockIds = readableBlocks.map((block) => block.id);
const tableOfContents = document.querySelector(".toc-details");
const desktopReader = window.matchMedia("(min-width: 768px)");
const appearanceDialog = document.querySelector("#appearance-dialog");
const appearanceButton = document.querySelector("#appearance-button");
const completeButton = document.querySelector("#chapter-complete-button");
const progressBar = document.querySelector("#reading-progress-bar");
const chapterProgressValue = document.querySelector("#chapter-progress-value");
const bookProgressValue = document.querySelector("#book-progress-value");

const fontFamilies = {
  serif: 'Georgia, "Times New Roman", serif',
  sans: 'Inter, ui-sans-serif, "Segoe UI", sans-serif',
  system: '-apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
};

const controls = {
  font: document.querySelector("#font-control"),
  textSize: document.querySelector("#text-size-control"),
  lineHeight: document.querySelector("#line-height-control"),
  pageMargin: document.querySelector("#page-margin-control"),
  contentWidth: document.querySelector("#content-width-control"),
};

const outputs = {
  textSize: document.querySelector("#text-size-output"),
  lineHeight: document.querySelector("#line-height-output"),
  pageMargin: document.querySelector("#page-margin-output"),
  contentWidth: document.querySelector("#content-width-output"),
};

function loadJson(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) ?? fallback;
  } catch {
    return fallback;
  }
}

function emptyBookState() {
  return { positions: {}, progress: {}, completed: [] };
}

let settings = normalizeSettings(loadJson(SETTINGS_KEY, DEFAULT_SETTINGS));
let bookState = { ...emptyBookState(), ...loadJson(bookStateKey, emptyBookState()) };
let appearanceAnchor = null;
bookState.positions ??= {};
bookState.progress ??= {};
bookState.completed ??= [];
for (const completedChapter of bookState.completed) {
  bookState.progress[completedChapter] = 100;
}

function saveBookState() {
  localStorage.setItem(bookStateKey, JSON.stringify(bookState));
}

function applySettings(nextSettings) {
  settings = normalizeSettings(nextSettings);
  document.documentElement.dataset.theme = settings.theme;
  document.documentElement.style.setProperty(
    "--reader-font",
    fontFamilies[settings.font],
  );
  document.documentElement.style.setProperty("--text-size", `${settings.textSize}px`);
  document.documentElement.style.setProperty("--line-height", settings.lineHeight);
  document.documentElement.style.setProperty(
    "--page-margin",
    `${settings.pageMargin}px`,
  );
  document.documentElement.style.setProperty(
    "--content-width",
    `${settings.contentWidth}ch`,
  );
  document.querySelector('meta[name="theme-color"]').content = getComputedStyle(
    document.documentElement,
  ).getPropertyValue("--paper");
  localStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
}

function synchronizeControls() {
  document.querySelector(`input[name="theme"][value="${settings.theme}"]`).checked =
    true;
  controls.font.value = settings.font;
  for (const key of ["textSize", "lineHeight", "pageMargin", "contentWidth"]) {
    controls[key].value = settings[key];
  }
  outputs.textSize.value = `${settings.textSize}px`;
  outputs.lineHeight.value = settings.lineHeight.toFixed(2);
  outputs.pageMargin.value = `${settings.pageMargin}px`;
  outputs.contentWidth.value = `${settings.contentWidth}ch`;
}

function settingsFromControls() {
  return normalizeSettings({
    theme: document.querySelector('input[name="theme"]:checked').value,
    font: controls.font.value,
    textSize: controls.textSize.value,
    lineHeight: controls.lineHeight.value,
    pageMargin: controls.pageMargin.value,
    contentWidth: controls.contentWidth.value,
  });
}

function synchronizeTableOfContents(event) {
  tableOfContents.open = event.matches;
}

function capturePosition() {
  if (!readableBlocks.length) {
    return null;
  }
  const readingLine = document.querySelector(".site-header").getBoundingClientRect().height + 16;
  let selectedBlock = readableBlocks[0];
  for (const block of readableBlocks) {
    if (block.getBoundingClientRect().top <= readingLine) {
      selectedBlock = block;
    } else {
      break;
    }
  }

  const rectangle = selectedBlock.getBoundingClientRect();
  const blockOffset = Math.min(
    1,
    Math.max(0, (readingLine - rectangle.top) / Math.max(rectangle.height, 1)),
  );
  const maximumScroll = Math.max(
    1,
    document.documentElement.scrollHeight - window.innerHeight,
  );
  return {
    blockId: selectedBlock.id,
    blockOffset,
    percentage: Math.round((window.scrollY / maximumScroll) * 100),
  };
}

function restorePosition(position) {
  const target = resolveReadingTarget(blockIds, position);
  if (!target) {
    return;
  }
  const block = document.getElementById(target.blockId);
  const headerHeight = document.querySelector(".site-header").getBoundingClientRect().height;
  const top =
    window.scrollY +
    block.getBoundingClientRect().top +
    block.getBoundingClientRect().height * target.blockOffset -
    headerHeight -
    14;
  window.scrollTo({ top: Math.max(0, top), behavior: "instant" });
}

function currentChapterProgress(position = capturePosition()) {
  if (bookState.completed.includes(chapterId)) {
    return 100;
  }
  return calculateChapterProgress(blockIds, position);
}

function renderCompletionState() {
  const completed = new Set(bookState.completed);
  for (const link of chapterLinks) {
    const isComplete = completed.has(link.dataset.chapterId);
    link.classList.toggle("is-complete", isComplete);
    link.querySelector(".completion-mark").hidden = !isComplete;
  }
  const chapterComplete = completed.has(chapterId);
  completeButton.classList.toggle("is-complete", chapterComplete);
  completeButton.setAttribute("aria-pressed", String(chapterComplete));
  completeButton.lastChild.textContent = chapterComplete
    ? " Marked complete"
    : " Mark chapter complete";
}

function renderProgress(position = capturePosition()) {
  const chapterProgress = currentChapterProgress(position);
  bookState.progress[chapterId] = Math.max(
    Number(bookState.progress[chapterId] ?? 0),
    chapterProgress,
  );
  const bookProgress = calculateBookProgress(chapterIds, bookState.progress);
  chapterProgressValue.textContent = `${chapterProgress}%`;
  bookProgressValue.textContent = `${bookProgress}%`;
  progressBar.style.width = `${chapterProgress}%`;
  document.title = `${chapterProgress}% · ${document.querySelector(".chapter-header h1").textContent} · DP-700 Study Reader`;
  saveBookState();
}

function saveCurrentPosition() {
  const position = capturePosition();
  if (!position) {
    return;
  }
  bookState.positions[chapterId] = position;
  renderProgress(position);
}

let scrollFrame = null;
window.addEventListener(
  "scroll",
  () => {
    if (scrollFrame !== null) {
      return;
    }
    scrollFrame = requestAnimationFrame(() => {
      saveCurrentPosition();
      scrollFrame = null;
    });
  },
  { passive: true },
);
window.addEventListener("pagehide", saveCurrentPosition);

appearanceButton.addEventListener("click", () => {
  appearanceAnchor = capturePosition();
  appearanceDialog.hidden = false;
});
appearanceDialog.addEventListener("input", () => {
  applySettings(settingsFromControls());
  synchronizeControls();
  requestAnimationFrame(() => {
    restorePosition(appearanceAnchor);
    renderProgress(appearanceAnchor);
  });
});
document.querySelector("#appearance-reset").addEventListener("click", () => {
  applySettings(DEFAULT_SETTINGS);
  synchronizeControls();
  requestAnimationFrame(() => {
    restorePosition(appearanceAnchor);
    renderProgress(appearanceAnchor);
  });
});
function closeAppearanceDialog() {
  const anchor = appearanceAnchor;
  appearanceDialog.hidden = true;
  requestAnimationFrame(() => {
    restorePosition(anchor);
    bookState.positions[chapterId] = anchor;
    renderProgress(anchor);
    appearanceAnchor = null;
  });
}
appearanceDialog
  .querySelector(".dialog-close")
  .addEventListener("click", closeAppearanceDialog);
window.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !appearanceDialog.hidden) {
    closeAppearanceDialog();
  }
});

completeButton.addEventListener("click", () => {
  const completed = new Set(bookState.completed);
  if (completed.has(chapterId)) {
    completed.delete(chapterId);
    delete bookState.progress[chapterId];
  } else {
    completed.add(chapterId);
    bookState.progress[chapterId] = 100;
  }
  bookState.completed = [...completed];
  renderCompletionState();
  renderProgress();
});

applySettings(settings);
synchronizeControls();
synchronizeTableOfContents(desktopReader);
desktopReader.addEventListener("change", synchronizeTableOfContents);
renderCompletionState();
requestAnimationFrame(() => {
  restorePosition(bookState.positions[chapterId]);
  renderProgress(bookState.positions[chapterId]);
});
