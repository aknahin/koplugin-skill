"use strict";
const assert = require("assert");
const { execFileSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const cli = path.join(__dirname, "..", "bin", "cli.js");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "kps-"));
const run = (...a) => execFileSync("node", [cli, ...a], { encoding: "utf8" });

run("install", "--dir", tmp);
const skill = path.join(tmp, "koplugin-skill");
for (const f of ["SKILL.md", "scripts/validate_plugin.py", "scripts/new_plugin.py", "assets/template.koplugin/main.lua", "references/pitfalls.md"])
  assert(fs.existsSync(path.join(skill, f)), `missing ${f}`);
assert(run("install", "--dir", tmp).includes("exists"), "second install must not overwrite without --force");
run("install", "--dir", tmp, "--force");
run("uninstall", "--dir", tmp);
assert(!fs.existsSync(skill), "uninstall failed");
fs.rmSync(tmp, { recursive: true, force: true });
console.log("ok");
