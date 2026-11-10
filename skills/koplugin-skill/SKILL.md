---
name: koplugin-skill
description: Build, review, debug and verify KOReader plugins (*.koplugin, Lua) for e-readers (Kobo, Kindle, PocketBook, Android) and the desktop emulator. Use whenever the user mentions KOReader, koplugin, koreader plugin, _meta.lua, WidgetContainer, registerToMainMenu, addToMainMenu, Dispatcher actions, UIManager, InfoMessage/InputDialog/Menu widgets, ./kodev, or wants to add a feature/menu item/gesture action to KOReader — even if they only say "e-reader plugin" or "make something for my Kobo/Kindle". Includes a scaffolder and a static validator for plugin structure, syntax and luacheck.
---

# KOReader plugin development

KOReader's frontend is plain Lua (LuaJIT) running on a small widget toolkit. A plugin is a directory named `<name>.koplugin/` with a `main.lua` (code) and `_meta.lua` (display info). There is no build step, so the fastest way to be correct is to follow the proven conventions below and verify with the bundled scripts instead of guessing at APIs.

Official docs: https://koreader.rocks/doc/ (API reference, generated from source) and the source at https://github.com/koreader/koreader (`plugins/` has ~40 real plugins; `plugins/hello.koplugin` is the minimal one). When unsure of a signature, check the module's doc page or read the source — KOReader APIs change between releases, and the docs site is the authority over memory.

## Workflow

1. **Scaffold** (new plugin): `python3 <skill>/scripts/new_plugin.py <id> "<Full Name>" [--dir <where>]` creates `<id>.koplugin/` from the template with menu entry, Dispatcher action, settings persistence and lifecycle hooks wired up. Edit from there rather than writing from scratch.
2. **Implement** using the patterns in this file; open the reference files only when you need them:
   - `references/plugin-anatomy.md` — file layout, loader rules, `is_doc_only`, init order, menu `sorting_hint` values
   - `references/ui-widgets.md` — InfoMessage, ConfirmBox, InputDialog, MultiInputDialog, Menu, ButtonDialog, SpinWidget, Notification, with working snippets
   - `references/events-and-lifecycle.md` — `onXxx` handlers, broadcasting, scheduling, Dispatcher, reader vs file-manager context
   - `references/settings-and-storage.md` — LuaSettings, G_reader_settings, per-book doc settings, DataStorage paths
   - `references/testing-and-verification.md` — emulator (`./kodev run`), luacheck, busted specs, on-device install and log reading
   - `references/pitfalls.md` — mistakes that crash KOReader or silently do nothing; skim before finishing
3. **Verify** (always, before saying it works): `python3 <skill>/scripts/validate_plugin.py <path/to/x.koplugin>`. It checks structure, `_meta.lua`, menu wiring, gettext usage, LuaJIT syntax (`luajit -bl`) and `luacheck` when those tools exist. Fix every ERROR; read every WARN. Then say honestly what was and wasn't verified — the validator cannot prove runtime behavior; only the emulator or a device can (see testing reference).

## The minimum viable plugin

```lua
-- _meta.lua
local _ = require("gettext")
return {
    fullname = _("My Plugin"),
    description = _([[One sentence shown in Plugin management.]]),
}
```

```lua
-- main.lua
local Dispatcher = require("dispatcher")
local InfoMessage = require("ui/widget/infomessage")
local UIManager = require("ui/uimanager")
local WidgetContainer = require("ui/widget/container/widgetcontainer")
local _ = require("gettext")

local MyPlugin = WidgetContainer:extend{
    name = "myplugin",        -- unique id, matches the dir prefix
    is_doc_only = false,      -- true = only loaded while a book is open
}

function MyPlugin:onDispatcherRegisterActions()
    Dispatcher:registerAction("myplugin_hello", {
        category = "none", event = "MyPluginHello",
        title = _("My Plugin: hello"), general = true,
    })
end

function MyPlugin:init()
    self:onDispatcherRegisterActions()
    self.ui.menu:registerToMainMenu(self)
end

function MyPlugin:addToMainMenu(menu_items)
    menu_items.myplugin = {
        text = _("My Plugin"),
        sorting_hint = "more_tools",
        callback = function() self:onMyPluginHello() end,
    }
end

function MyPlugin:onMyPluginHello()
    UIManager:show(InfoMessage:new{ text = _("Hello from my plugin") })
    return true  -- event consumed
end

return MyPlugin
```

## Rules that matter (and why)

- **Wrap every user-visible string in `_()`** — KOReader is translated through gettext; unwrapped strings can never be localized. Use `T = require("ffi/util").template` for interpolation (`T(_("Page %1"), n)`), not `..` concatenation, because word order differs by language.
- **Events are methods named `on<EventName>`**; return `true` only when you consumed the event, otherwise other widgets (including core KOReader) stop receiving it.
- **Never block the UI thread.** Network calls, big file scans and `os.execute` freeze a single-threaded e-ink device. Use `NetworkMgr:runWhenOnline`, `UIManager:scheduleIn`, `Trapper:wrap` (subprocess + progress) for long work.
- **Persist with `LuaSettings`, flush deliberately.** Settings files live in `DataStorage:getSettingsDir()`; call `:flush()` after changes (or in `onFlushSettings`) — a crash or battery death otherwise loses them.
- **Clean up** timers (`UIManager:unschedule(fn)`) and widgets you opened in `onCloseWidget`/`onCloseDocument`; leaked scheduled callbacks keep waking the device and drain battery.
- **E-ink aware UI**: prefer `InfoMessage` with `timeout`, avoid animations, keep refreshes minimal (`UIManager:setDirty(widget, "ui")` only on the widget that changed).
- **Use `logger`** (`require("logger")`; `logger.dbg/info/warn/err`) rather than `print`; output goes to stdout in the emulator and `crash.log` on device.
- **Guard optional dependencies** (`self.ui.statistics`, `self.ui.document`, `Device:hasFrontlight()`): the same plugin can load in the file manager or on devices without the feature.

## Reporting back

State what you created/changed, the exact validator command and its result, and what remains unverified (e.g. "not run in the emulator"). If the validator or luacheck was unavailable, say so rather than implying a clean pass.
