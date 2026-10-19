import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import vm from "node:vm";

test("all inline browser scripts parse", async () => {
  const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
  const scripts = [...html.matchAll(/<script\b[^>]*>([\s\S]*?)<\/script>/g)];
  for (const [, source] of scripts) new vm.Script(source);
});

test("bridge suggestions refer to their own chunk, including the last chunk", async () => {
  const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
  const source = "function rRO(d)" + html.split("function rRO(d)")[1].split("\nfunction ")[0];
  const nodes = { roc: { innerHTML: "" }, cov: { innerHTML: "" } };
  const context = vm.createContext({ document: { getElementById: (id) => nodes[id] }, esc: (text) => text });
  vm.runInContext(source, context);
  context.rRO({ chunks: [
    { order: 1, text: "First", concepts: ["Mass"], prerequisites: [] },
    { order: 2, text: "Second", concepts: ["Acceleration"], prerequisites: ["Mass"] },
  ], dropoutPerChunk: [50, 60] });
  assert.match(nodes.roc.innerHTML, /Bridge before Chunk 1/);
  assert.match(nodes.roc.innerHTML, /Bridge before Chunk 2/);
  assert.doesNotMatch(nodes.roc.innerHTML, /Bridge before Chunk 3/);
  assert.match(nodes.roc.innerHTML, /Before introducing "Acceleration".*connection to "Mass"/);
});
