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

test("rejecting oversized media clears a previously selected lesson", async () => {
  const html = await readFile(new URL("../index.html", import.meta.url), "utf8");
  const functions = ["hf", "cf", "ss", "esc", "fB", "gExt", "gIco"];
  const source = functions.map((name) => "function " + name + html.split("function " + name)[1].split("\n")[0]).join("\n");
  const nodes = Object.fromEntries(["fpw", "mpv", "aBtn", "uSt", "fi"].map((id) => [id, {
    innerHTML: "", value: "", disabled: true,
    classList: { add() {}, remove() {} }, appendChild() {},
  }]));
  const context = vm.createContext({ document: {
    getElementById: (id) => nodes[id],
    createElement: () => ({}),
  } });
  vm.runInContext("let cFile=null,cType=null; const VE=['mp4','mov','webm'],AE=['mp3','wav','m4a','ogg'],DE=['pdf','docx','pptx','txt'],IE=['png','jpg','jpeg']; const fi=document.getElementById('fi');\n" + source, context);

  context.hf({ name: "lesson.txt", size: 100 });
  assert.equal(vm.runInContext("cFile.name", context), "lesson.txt");
  assert.equal(nodes.aBtn.disabled, false);
  nodes.fi.value = "C:\\fakepath\\recording.wav";

  context.hf({ name: "recording.wav", size: 26 * 1024 * 1024 });
  assert.equal(vm.runInContext("cFile", context), null);
  assert.equal(vm.runInContext("cType", context), null);
  assert.equal(nodes.fi.value, "");
  assert.equal(nodes.fpw.innerHTML, "");
  assert.equal(nodes.mpv.innerHTML, "");
  assert.equal(nodes.aBtn.disabled, true);
  assert.equal(nodes.uSt.className, "status error");
  assert.equal(nodes.uSt.textContent, ">25MB");
});
