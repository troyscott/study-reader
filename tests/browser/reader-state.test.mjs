import test from "node:test";
import assert from "node:assert/strict";

import {
  DEFAULT_SETTINGS,
  calculateBookProgress,
  calculateChapterProgress,
  normalizeSettings,
  resolveReadingTarget,
} from "../../src/study_reader/reader/static/reader-state.js";

test("appearance settings are normalized into supported ranges", () => {
  assert.deepEqual(
    normalizeSettings({
      theme: "unknown",
      font: "sans",
      textSize: 40,
      lineHeight: 0.5,
      pageMargin: 4,
      contentWidth: 200,
    }),
    {
      ...DEFAULT_SETTINGS,
      font: "sans",
      textSize: 24,
      lineHeight: 1.4,
      pageMargin: 12,
      contentWidth: 82,
    },
  );
});

test("stable block identity survives content growth before the saved passage", () => {
  const position = { blockId: "decision-table", blockOffset: 0.4, percentage: 60 };
  const grownContent = ["orientation", "new-context", "decision-table", "recall"];

  assert.deepEqual(resolveReadingTarget(grownContent, position), {
    blockId: "decision-table",
    blockIndex: 2,
    blockOffset: 0.4,
    restoredBy: "block",
  });
  assert.equal(calculateChapterProgress(grownContent, position), 60);
});

test("percentage fallback restores position when a block was removed", () => {
  const blocks = ["orientation", "decision-table", "recall", "source"];
  const position = { blockId: "removed-block", blockOffset: 0.8, percentage: 75 };

  assert.deepEqual(resolveReadingTarget(blocks, position), {
    blockId: "source",
    blockIndex: 3,
    blockOffset: 0,
    restoredBy: "percentage",
  });
  assert.equal(calculateChapterProgress(blocks, position), 75);
});

test("whole-book progress remains deterministic when chapters are reordered", () => {
  const progress = { workspace: 100, lifecycle: 40, security: 0 };

  assert.equal(
    calculateBookProgress(["workspace", "lifecycle", "security"], progress),
    47,
  );
  assert.equal(
    calculateBookProgress(["security", "workspace", "lifecycle"], progress),
    47,
  );
});

test("empty books and chapters have zero progress", () => {
  assert.equal(calculateChapterProgress([], null), 0);
  assert.equal(calculateBookProgress([], {}), 0);
});
