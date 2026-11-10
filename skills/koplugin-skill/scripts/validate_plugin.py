#!/usr/bin/env python3
"""Static validator for KOReader plugins (*.koplugin).

Usage: validate_plugin.py <plugin_dir> [--strict] [--json]

Checks structure, _meta.lua, main.lua conventions, menu/Dispatcher wiring,
gettext usage, LuaJIT syntax (if `luajit` is installed) and luacheck (if
installed). Exit code: 0 = no errors, 1 = errors (or warnings with --strict),
2 = bad usage. Static checks cannot prove runtime behavior; run the plugin in
the KOReader emulator (`./kodev run`) for that.
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


def strip_lua_comments(src: str) -> str:
    """Remove --[[ ]] / --[=[ ]=] block comments and -- line comments (string-unaware but good enough for heuristics)."""
    src = re.sub(r"--\[(=*)\[.*?\]\1\]", "", src, flags=re.S)
    return re.sub(r"--[^\n]*", "", src)


class Report:
    def __init__(self):
        self.items = []  # (level, file, message)

    def add(self, level, file, msg):
        self.items.append((level, file, msg))

    def count(self, level):
        return sum(1 for i in self.items if i[0] == level)


def check_syntax(path: Path, rep: Report, rel: str):
    luajit = shutil.which("luajit")
    if not luajit:
        return False
    r = subprocess.run([luajit, "-bl", str(path)], capture_output=True, text=True)
    if r.returncode != 0:
        rep.add("ERROR", rel, "syntax: " + (r.stderr.strip().splitlines() or ["luajit failed"])[0])
    return True


def validate(plugin: Path, rep: Report):
    if not plugin.is_dir():
        rep.add("ERROR", str(plugin), "not a directory")
        return
    if not plugin.name.endswith(".koplugin"):
        rep.add("ERROR", plugin.name, "directory name must end with '.koplugin' or KOReader will ignore it")
    stem = plugin.name[: -len(".koplugin")] if plugin.name.endswith(".koplugin") else plugin.name

    main, meta = plugin / "main.lua", plugin / "_meta.lua"
    for f in (main, meta):
        if not f.is_file():
            rep.add("ERROR", f.name, "missing required file")

    lua_files = sorted(plugin.rglob("*.lua"))
    have_luajit = False
    for f in lua_files:
        have_luajit = check_syntax(f, rep, str(f.relative_to(plugin))) or have_luajit
    if not have_luajit:
        rep.add("INFO", "-", "luajit not found: syntax check skipped (brew install luajit)")

    # ---- _meta.lua
    if meta.is_file():
        m = strip_lua_comments(meta.read_text(encoding="utf-8", errors="replace"))
        if not re.search(r"\bfullname\s*=", m):
            rep.add("ERROR", "_meta.lua", "missing `fullname`")
        if not re.search(r"\bdescription\s*=", m):
            rep.add("ERROR", "_meta.lua", "missing `description`")
        if re.search(r"(?<![\w.])name\s*=", m):
            rep.add("WARN", "_meta.lua", "`name` in _meta.lua is deprecated and ignored by the loader; set it in main.lua")
        if not re.search(r"require\(\s*[\"']gettext[\"']\s*\)", m):
            rep.add("WARN", "_meta.lua", "does not require gettext; fullname/description should be wrapped in _()")

    # ---- main.lua
    if main.is_file():
        raw = main.read_text(encoding="utf-8", errors="replace")
        s = strip_lua_comments(raw)
        disabled_stub = re.search(r"return\s*\{\s*disabled\s*=\s*true", s)
        if not re.search(r"^\s*return\b", s, flags=re.M):
            rep.add("ERROR", "main.lua", "must `return` the plugin class (or { disabled = true })")
        if not disabled_stub:
            if not re.search(r"WidgetContainer\s*:\s*extend", s):
                rep.add("WARN", "main.lua", "plugin class should be WidgetContainer:extend{...}")
            nm = re.search(r"\bname\s*=\s*[\"']([^\"']+)[\"']", s)
            if not nm:
                rep.add("ERROR", "main.lua", "class table has no `name = \"...\"` (unique plugin id)")
            else:
                pid = nm.group(1)
                if pid != stem:
                    rep.add("WARN", "main.lua", f"name '{pid}' differs from directory prefix '{stem}' (convention: identical)")
                if pid in {"menu", "document", "view", "statistics", "highlight", "bookmark", "link", "dictionary", "rolling", "paging", "toc", "gesture", "gestures"}:
                    rep.add("ERROR", "main.lua", f"name '{pid}' collides with a core module on self.ui")
            if not re.search(r"is_doc_only\s*=", s):
                rep.add("INFO", "main.lua", "is_doc_only not set; plugin will also load in the file manager (self.ui.document is nil there)")

            registers_menu = re.search(r"registerToMainMenu\s*\(", s)
            defines_menu = re.search(r"function\s+\w+[.:]addToMainMenu\s*\(", s)
            if registers_menu and not defines_menu:
                rep.add("ERROR", "main.lua", "registerToMainMenu(self) called but no addToMainMenu method defined")
            if defines_menu and not registers_menu:
                rep.add("ERROR", "main.lua", "addToMainMenu defined but never registered: add self.ui.menu:registerToMainMenu(self) in init()")
            if defines_menu and "sorting_hint" not in s:
                rep.add("INFO", "main.lua", "no sorting_hint: fine only if the menu key is listed in KOReader's *_menu_order.lua; otherwise set e.g. sorting_hint = \"more_tools\"")
            if not re.search(r"function\s+\w+[.:]init\s*\(", s):
                rep.add("WARN", "main.lua", "no init(); nothing registers the menu/actions")

            # Dispatcher event -> handler
            for ev in re.findall(r"registerAction\s*\([^)]*?event\s*=\s*[\"'](\w+)[\"']", s, flags=re.S):
                if not re.search(r"function\s+\w+[.:]on" + re.escape(ev) + r"\s*\(", s):
                    rep.add("ERROR", "main.lua", f"Dispatcher action event '{ev}' has no handler function on{ev}()")
            if "registerAction" in s and "dispatcher" not in s:
                rep.add("ERROR", "main.lua", "uses Dispatcher but does not require(\"dispatcher\")")

            # scheduling hygiene
            if re.search(r"scheduleIn|UIManager:schedule", s) and "unschedule" not in s:
                rep.add("WARN", "main.lua", "schedules callbacks but never unschedules; leaked timers wake the device (unschedule in onCloseWidget/onSuspend)")
            # settings hygiene
            if re.search(r"LuaSettings\s*:\s*open", s) and not re.search(r"flush\s*\(", s):
                rep.add("WARN", "main.lua", "LuaSettings opened but never flush()ed; settings are lost on crash")

        # general lint-ish heuristics on all lua files
    for f in lua_files:
        rel = str(f.relative_to(plugin))
        s = strip_lua_comments(f.read_text(encoding="utf-8", errors="replace"))
        if re.search(r"(?<![\w.:])print\s*\(", s):
            rep.add("WARN", rel, "uses print(); use require(\"logger\") (logger.dbg/info/warn/err)")
        if re.search(r"\b(os\.execute|io\.popen)\s*\(", s):
            rep.add("WARN", rel, "os.execute/io.popen blocks the UI thread and may be unavailable on some platforms; use Trapper/subprocess and guard by Device")
        if re.search(r"\bdofile\s*\(|\bloadstring\s*\(", s):
            rep.add("WARN", rel, "dynamic code loading (dofile/loadstring); make sure input is trusted")
        uses_gt = re.search(r"(?<![\w.])_\s*\(", s)
        if uses_gt and not re.search(r"local\s+_\s*=\s*require\(\s*[\"']gettext[\"']\s*\)", s):
            rep.add("ERROR", rel, "calls _() but has no `local _ = require(\"gettext\")`")
        for ln, line in enumerate(s.splitlines(), 1):
            if re.search(r"\b(text|title|title_text|ok_text|cancel_text)\s*=\s*\"[A-Za-z][^\"]*\"", line) and "_(" not in line:
                rep.add("WARN", f"{rel}:{ln}", "user-visible string literal not wrapped in _() (cannot be translated)")
                break

    # ---- luacheck
    lc = shutil.which("luacheck")
    if lc:
        cfg = plugin / ".luacheckrc"
        cmd = [lc, "--no-color", "--codes"]
        if cfg.is_file():
            cmd += ["--config", str(cfg)]
        else:
            cmd += ["--std", "luajit", "--no-self", "--globals", "G_reader_settings", "G_defaults", "--ignore", "631"]
        r = subprocess.run(cmd + [str(plugin)], capture_output=True, text=True)
        if r.returncode != 0:
            for line in r.stdout.splitlines():
                if re.search(r":\d+:\d+:", line):
                    rep.add("WARN", "luacheck", line.strip().replace(str(plugin) + "/", ""))
    else:
        rep.add("INFO", "-", "luacheck not found: lint skipped (luarocks install luacheck / brew install luacheck)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("plugin")
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    a = ap.parse_args()

    rep = Report()
    validate(Path(a.plugin).expanduser().resolve(), rep)

    if a.json:
        print(json.dumps([{"level": l, "where": w, "message": m} for l, w, m in rep.items], indent=2))
    else:
        for level, where, msg in rep.items:
            print(f"{level:5} {where}: {msg}")
        print(f"\n{rep.count('ERROR')} error(s), {rep.count('WARN')} warning(s), {rep.count('INFO')} note(s)")
        print("Static checks only: run in the KOReader emulator or on a device to verify runtime behavior.")
    failed = rep.count("ERROR") > 0 or (a.strict and rep.count("WARN") > 0)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
