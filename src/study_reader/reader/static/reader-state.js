export const DEFAULT_SETTINGS = Object.freeze({
  theme: "sepia",
  font: "serif",
  textSize: 17,
  lineHeight: 1.78,
  pageMargin: 48,
  contentWidth: 68,
});

const THEMES = new Set(["white", "sepia", "grey", "dark"]);
const FONTS = new Set(["serif", "sans", "system"]);

function clamp(value, minimum, maximum) {
  return Math.min(maximum, Math.max(minimum, value));
}

function numberOrDefault(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function normalizeSettings(candidate = {}) {
  return {
    theme: THEMES.has(candidate.theme) ? candidate.theme : DEFAULT_SETTINGS.theme,
    font: FONTS.has(candidate.font) ? candidate.font : DEFAULT_SETTINGS.font,
    textSize: clamp(
      numberOrDefault(candidate.textSize, DEFAULT_SETTINGS.textSize),
      15,
      24,
    ),
    lineHeight: clamp(
      numberOrDefault(candidate.lineHeight, DEFAULT_SETTINGS.lineHeight),
      1.4,
      2.1,
    ),
    pageMargin: clamp(
      numberOrDefault(candidate.pageMargin, DEFAULT_SETTINGS.pageMargin),
      12,
      96,
    ),
    contentWidth: clamp(
      numberOrDefault(candidate.contentWidth, DEFAULT_SETTINGS.contentWidth),
      42,
      82,
    ),
  };
}

export function resolveReadingTarget(blockIds, position) {
  if (!blockIds.length || !position) {
    return null;
  }

  const stableIndex = blockIds.indexOf(position.blockId);
  if (stableIndex >= 0) {
    return {
      blockId: blockIds[stableIndex],
      blockIndex: stableIndex,
      blockOffset: clamp(numberOrDefault(position.blockOffset, 0), 0, 1),
      restoredBy: "block",
    };
  }

  const percentage = clamp(numberOrDefault(position.percentage, 0), 0, 100);
  const fallbackIndex = Math.min(
    blockIds.length - 1,
    Math.floor((percentage / 100) * blockIds.length),
  );
  return {
    blockId: blockIds[fallbackIndex],
    blockIndex: fallbackIndex,
    blockOffset: 0,
    restoredBy: "percentage",
  };
}

export function calculateChapterProgress(blockIds, position) {
  if (!blockIds.length || !position) {
    return 0;
  }

  const blockIndex = blockIds.indexOf(position.blockId);
  if (blockIndex < 0) {
    return Math.round(
      clamp(numberOrDefault(position.percentage, 0), 0, 100),
    );
  }

  const blockOffset = clamp(numberOrDefault(position.blockOffset, 0), 0, 1);
  return Math.round(((blockIndex + blockOffset) / blockIds.length) * 100);
}

export function calculateBookProgress(chapterIds, progressByChapter) {
  if (!chapterIds.length) {
    return 0;
  }

  const total = chapterIds.reduce(
    (sum, chapterId) =>
      sum + clamp(numberOrDefault(progressByChapter[chapterId], 0), 0, 100),
    0,
  );
  return Math.round(total / chapterIds.length);
}
