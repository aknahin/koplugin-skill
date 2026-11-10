# Testing and verification

Verification is layered; report which layers you actually ran.

| Layer | Command | Catches |
|-------|---------|---------|
| 1. Static | `python3 scripts/validate_plugin.py my.koplugin` | structure, `_meta`, menu wiring, gettext, syntax, luacheck |
| 2. Lint | `luacheck my.koplugin` (uses `.luacheckrc`) | undefined globals, unused vars, shadowing |
| 3. Emulator | `./kodev run` in a KOReader checkout | real load, menu appearance, runtime errors |
| 4. Specs | `./kodev test front` (busted) | logic regressions |
| 5. Device | copy to device, restart | hardware-specific behavior, performance |

## 1–2. Static

Syntax: `luajit -bl file.lua > /dev/null` (non-zero exit = syntax error; LuaJIT is the runtime KOReader uses, so 5.1 syntax + LuaJIT extensions apply — no `goto` surprises, no integer division `//`, no `<const>`).

luacheck: install via `luarocks install luacheck` or `brew install luacheck`. KOReader's own config (`.luacheckrc`) sets `std = "luajit"`, `self = false` (ignore implicit self), allows globals `G_reader_settings`, `G_defaults`, and ignores warning 631 (line length). The template copies those settings so your plugin lints the same way upstream CI would.

## 3. Emulator

```bash
git clone https://github.com/koreader/koreader.git && cd koreader
./kodev fetch-thirdparty          # first time
./kodev build                     # first time (needs the toolchain from the Building docs)
./kodev run                       # launches the SDL emulator (Linux/macOS)
./kodev run -d                    # debug logging
./kodev run /path/to/book.epub    # open a book directly
```

Install your plugin into the emulator by symlinking it into the checkout's `plugins/` folder (or the emulator data dir's `plugins/`):

```bash
ln -s "$PWD/../myplugin.koplugin" plugins/myplugin.koplugin
```

Then: Tools (gear/wrench) → More tools → **Plugin management** to confirm the plugin is listed with your `fullname`; open your menu entry; trigger the Dispatcher action from Settings → Taps and gestures. Watch the terminal for Lua tracebacks. Relaunch after every code change.

Prototype widgets without the whole UI: `./kodev wbuilder` (runs `tools/wbuilder.lua`; add your own `UIManager:show` calls).

macOS/Linux shortcuts in the emulator: keyboard arrows/page keys emulate buttons; mouse = touch; `Ctrl+Q`/`Esc` exits.

## 4. Specs (busted)

KOReader specs live in `spec/unit/` of the main repo; helpers `load_plugin`, `disable_plugins`, `fastforward_ui_events` are provided to specs (they are listed in KOReader's `.luacheckrc`). Run `./kodev test front` or a single file with `./kodev test front <name>`; list with `./kodev test -l`. For standalone plugin repos, keep pure logic in a separate module (`myplugin_core.lua`) with no KOReader requires so plain `busted` can test it, and keep `main.lua` a thin UI layer.

## 5. On device

| Device | Plugins folder |
|--------|---------------|
| Kobo | `.adds/koreader/plugins/` |
| Kindle | `/mnt/us/koreader/plugins/` |
| PocketBook | `applications/koreader/plugins/` |
| Android | `<storage>/koreader/plugins/` |
| Cervantes/others | `koreader/plugins/` under the install dir |

Copy the whole `*.koplugin` folder, eject, restart KOReader (Tools → Exit/Restart). Logs: `crash.log` in the koreader directory (errors + `logger` output; enable verbose via Developer options → Enable debug logging). If the plugin doesn't show up in Plugin management: wrong folder suffix, `_meta.lua` error, or `main.lua` failed to load — check `crash.log` for `PluginLoader` lines.

## Verification checklist before declaring done

- [ ] `validate_plugin.py` → 0 errors, warnings reviewed
- [ ] luacheck clean (or unavailability disclosed)
- [ ] Loads in Plugin management with correct name/description
- [ ] Menu entry appears in the intended place and works in **both** reader and file manager (unless `is_doc_only`)
- [ ] Settings persist across restart
- [ ] No leaked timers after closing the book / suspending (grep for every `scheduleIn` has an `unschedule`)
- [ ] All user strings go through `_()`
- [ ] Works with no network / no document / device without frontlight where relevant
