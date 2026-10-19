import { mkdir, copyFile, writeFile } from "node:fs/promises";

await mkdir(new URL("../dist/", import.meta.url), { recursive: true });
await copyFile(new URL("../index.html", import.meta.url), new URL("../dist/index.html", import.meta.url));
// Private local configuration must never enter the public browser artifact.
await writeFile(new URL("../dist/config.js", import.meta.url), "window.__LUCIDA_CONFIG = {};\n");
