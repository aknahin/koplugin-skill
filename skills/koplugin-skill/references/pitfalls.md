# Pitfalls

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Plugin not listed in Plugin management | Folder not named `*.koplugin`, nested one level too deep after unzip, or Lua error at load | Check path `plugins/x.koplugin/main.lua`; read `crash.log` |
| Menu item missing | Forgot `self.ui.menu:registerToMainMenu(self)` in `init`, or `addToMainMenu` misspelled, or duplicate menu key | Match the exact names; make the key unique (`myplugin_…`) |
| Menu item appears in wrong tab | `sorting_hint` wrong/absent | Use `more_tools`, `tools`, `setting`, `search`, `navi`, `typeset`, `main` |
| `attempt to index field 'document' (a nil value)` | Plugin loads in the file manager too | `is_doc_only = true` or guard `self.ui.document` |
| `attempt to call method 'x' (a nil value)` on `self.ui.foo` | Other plugin disabled / not initialised yet | nil-check; use `registerPostInitCallback` |
| Gesture/hotkey action doesn't fire | `event` name ≠ `on<Event>` method, or handler returned nothing and parent consumed | Match names exactly; the handler must exist on your plugin class |
| Core feature stops working after your plugin loads | Your `onXxx` returned `true` and swallowed a core event | Return `true` only for events that are yours |
| Settings lost after crash | Never `flush()`ed | Flush on change and in `onFlushSettings` |
| Battery drain / phantom actions | `scheduleIn` loop never unscheduled | Keep a stable function ref; `unschedule` in `onCloseWidget`/`onSuspend` |
| UI freezes on WiFi/HTTP | Blocking socket on UI thread, no timeout | `NetworkMgr:runWhenOnline`, `socketutil` timeouts, `Trapper` subprocess |
| `module 'ui/widget/xyz' not found` | Wrong path (slash style from `frontend/`) | Paths are relative to `frontend/`: `ui/widget/infomessage` (lowercase, no `.lua`) |
| Strings never translate | Missing `_()` or `local _ = require("gettext")` | Add both |
| Global variable leak | Missing `local` | Run luacheck |
| Works in emulator, not on device | Hard-coded `/home/...` paths, `io.popen` of non-existent tools, fonts/glyphs | Use `DataStorage`, avoid shell tools or gate by `Device` |
| Code edits don't apply | Modules cached | Restart KOReader / relaunch emulator |

## Style that upstream accepts

- 4-space indent, `local` everything, `CamelCase` classes, `snake_case` functions/locals in newer code (methods on the class are `camelCase`: `Hello:addToMainMenu`).
- Requires at top, alphabetical; core `require("ui/...")` paths with slashes.
- Doc comment header:
  ```lua
  --[[--
  One-line description.

  @module koplugin.MyPlugin
  --]]--
  ```
  (this feeds the generated docs on koreader.rocks).
- No trailing logic in `_meta.lua` beyond gettext + the returned table.

## Safety

- Don't execute downloaded code, don't `os.execute` unsanitized user input, and don't store credentials in plain `G_reader_settings` unless the user is told.
- Respect `Device:canExecuteScript` / platform limits; guard `os.execute` for Android sandboxing.
