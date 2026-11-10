#!/usr/bin/env node
"use strict";
// koplugin-skill installer: copies the skill folder into the skills directory of your AI agent(s).
const fs = require("fs");
const os = require("os");
const path = require("path");

const SKILL = "koplugin-skill";
const SRC = path.join(__dirname, "..", "skills", SKILL);
const HOME = os.homedir();

// All of these agents read Agent Skills folders (SKILL.md + resources).
const AGENTS = {
  claude: { global: path.join(HOME, ".claude", "skills"), project: path.join(".claude", "skills"), label: "Claude Code" },
  codex: { global: path.join(HOME, ".codex", "skills"), project: path.join(".codex", "skills"), label: "OpenAI Codex CLI" },
  gemini: { global: path.join(HOME, ".gemini", "skills"), project: path.join(".gemini", "skills"), label: "Gemini CLI" },
  opencode: { global: path.join(HOME, ".config", "opencode", "skills"), project: path.join(".opencode", "skills"), label: "OpenCode" },
  cursor: { global: path.join(HOME, ".cursor", "skills"), project: path.join(".cursor", "skills"), label: "Cursor" },
  agents: { global: path.join(HOME, ".agents", "skills"), project: path.join(".agents", "skills"), label: "Generic (.agents/skills)" },
};

function usage() {
  console.log(`koplugin-skill — KOReader plugin development skill for AI coding agents

Usage:
  npx koplugin-skill [install] [options]
  npx koplugin-skill uninstall [options]
  npx koplugin-skill list

Options:
  -a, --agent <names>   comma list: ${Object.keys(AGENTS).join(", ")}  (default: claude)
      --all             every agent above
  -p, --project         install into the current project instead of your home dir
  -d, --dir <path>      install into <path>/${SKILL} (any agent that reads SKILL.md folders)
  -f, --force           overwrite an existing install
      --dry-run         show what would happen
  -h, --help
`);
}

function parse(argv) {
  const o = { cmd: "install", agents: [], project: false, force: false, dry: false, dir: null, all: false };
  const rest = [...argv];
  if (rest[0] && !rest[0].startsWith("-")) o.cmd = rest.shift();
  while (rest.length) {
    const a = rest.shift();
    if (a === "-a" || a === "--agent") o.agents.push(...String(rest.shift() || "").split(",").filter(Boolean));
    else if (a === "--all") o.all = true;
    else if (a === "-p" || a === "--project") o.project = true;
    else if (a === "-d" || a === "--dir") o.dir = rest.shift();
    else if (a === "-f" || a === "--force") o.force = true;
    else if (a === "--dry-run") o.dry = true;
    else if (a === "-h" || a === "--help") o.cmd = "help";
    else { console.error(`Unknown option: ${a}`); process.exit(2); }
  }
  return o;
}

function targets(o) {
  if (o.dir) return [{ name: "custom", base: path.resolve(o.dir) }];
  let names = o.all ? Object.keys(AGENTS) : o.agents.length ? o.agents : ["claude"];
  return names.map((n) => {
    if (!AGENTS[n]) { console.error(`Unknown agent '${n}'. Choose from: ${Object.keys(AGENTS).join(", ")}`); process.exit(2); }
    const base = o.project ? path.resolve(AGENTS[n].project) : AGENTS[n].global;
    return { name: n, base };
  });
}

function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, e.name), d = path.join(dst, e.name);
    if (e.isDirectory()) copyDir(s, d);
    else { fs.copyFileSync(s, d); fs.chmodSync(d, fs.statSync(s).mode); }
  }
}

function main() {
  const o = parse(process.argv.slice(2));
  if (o.cmd === "help") return usage();
  if (o.cmd === "list") {
    for (const [k, v] of Object.entries(AGENTS)) console.log(`${k.padEnd(9)} ${v.label.padEnd(26)} global: ${v.global}  project: ${v.project}`);
    return;
  }
  if (o.cmd !== "install" && o.cmd !== "uninstall") { usage(); process.exit(2); }

  for (const t of targets(o)) {
    const dest = path.join(t.base, SKILL);
    if (o.cmd === "uninstall") {
      if (!fs.existsSync(dest)) { console.log(`- ${t.name}: not installed (${dest})`); continue; }
      if (!o.dry) fs.rmSync(dest, { recursive: true, force: true });
      console.log(`✓ ${t.name}: removed ${dest}${o.dry ? " (dry run)" : ""}`);
      continue;
    }
    if (fs.existsSync(dest) && !o.force) { console.log(`- ${t.name}: ${dest} exists (use --force to overwrite)`); continue; }
    if (!o.dry) {
      fs.rmSync(dest, { recursive: true, force: true });
      copyDir(SRC, dest);
    }
    console.log(`✓ ${t.name}: installed to ${dest}${o.dry ? " (dry run)" : ""}`);
  }
  if (o.cmd === "install") console.log(`\nRestart your agent, then ask e.g. "create a KOReader plugin that ...".\nHelper scripts: python3 <skill>/scripts/{new_plugin,validate_plugin}.py`);
}

main();
