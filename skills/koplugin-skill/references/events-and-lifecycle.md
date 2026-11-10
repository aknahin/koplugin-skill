# Events, scheduling and Dispatcher

## How events work (from the official Events topic)

An event has a `handler` name and `args`. A widget receiving event `Foo` calls `self.onFoo(self, ...)` if it exists. Events propagate **child widgets first**, then the container itself; a handler that returns `true` consumes the event and stops propagation.

```lua
local Event = require("ui/event")
UIManager:sendEvent(Event:new("MyEvent", arg1))       -- from the topmost widget downward
UIManager:broadcastEvent(Event:new("MyEvent", arg1))  -- to every widget on the stack
self.ui:handleEvent(Event:new("MyEvent"))             -- into the current reader/file manager tree
```

Your plugin is a child of the ReaderUI/FileManager container, so defining `function MyPlugin:onSomething(...)` is enough to receive `Something`.

## Events plugins commonly handle

Names below are used by core plugins; confirm in source (`grep -rn "onEventName" frontend plugins`) for the release you target.

| Handler | When |
|---------|------|
| `onReaderReady()` | Document loaded and rendered (reader only) |
| `onCloseDocument()` | Book is closing — save per-book state |
| `onPageUpdate(pageno)` / `onPosUpdate(pos)` | Page changed (paging / rolling docs) |
| `onFlushSettings()` | KOReader asks everyone to persist — call `self.settings:flush()` |
| `onSuspend()` / `onResume()` | Device sleep/wake — stop/restart timers, networking |
| `onNetworkConnected()` / `onNetworkDisconnected()` | WiFi state |
| `onCloseWidget()` | The plugin container is torn down — unschedule |
| `onExit()` / `onQuit()` | App shutting down |

## Scheduling

```lua
UIManager:scheduleIn(30, self.tick)        -- run self.tick(…) in 30 s (same function ref needed to cancel)
UIManager:unschedule(self.tick)
UIManager:nextTick(function() … end)       -- after current event loop turn
UIManager:setDirty(widget, "ui")           -- request repaint; modes: "ui", "partial", "flashui", "full"
```

Use a stable function reference for anything you will `unschedule` (store it on `self` in `init`, e.g. `self.tick = function() … end`). Anonymous inline closures cannot be cancelled.

## Dispatcher (gestures, profiles, hotkeys)

Registering an action makes it assignable in Settings → Taps and gestures, Profiles, and Hotkeys:

```lua
local Dispatcher = require("dispatcher")
Dispatcher:registerAction("myplugin_toggle", {
    category = "none",            -- none | arg | absolutenumber | incrementalnumber | string
    event = "MyPluginToggle",     -- handled by function MyPlugin:onMyPluginToggle()
    title = _("My plugin: toggle"),
    general = true,               -- available everywhere; or reader = true / device = true / screen = true /
                                  -- rolling = true / paging = true / filemanager = true  (section flags)
    separator = false,
})
-- for numeric/string categories: min, max, step, default, args, toggle
```

Call `registerAction` from `init` (re-registering is idempotent). The handler receives the argument for `arg`/number categories: `function MyPlugin:onMyPluginSet(value) … return true end`.

## Reader vs. file manager checks

```lua
if self.ui.document then … end                    -- a book is open
if self.ui.rolling then … end                     -- reflowable (EPUB/FB2…)
if self.ui.paging then … end                      -- fixed layout (PDF/DJVU/CBZ)
local Device = require("device")
Device:isKindle() / :isKobo() / :isAndroid() / :hasFrontlight() / :isTouchDevice() / :hasKeys()
```

## Sending data to other plugins

`self.ui.<otherplugin>` is the loaded instance (may be `nil` if disabled) — always nil-check. For loose coupling prefer broadcasting an event.
