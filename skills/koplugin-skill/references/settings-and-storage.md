# Settings and storage

## Paths (`require("datastorage")`)

```lua
local DataStorage = require("datastorage")
DataStorage:getDataDir()       -- KOReader data dir (on Android/Kobo/Kindle: the koreader folder; emulator: repo's koreader/ or $EMU_DIR)
DataStorage:getSettingsDir()   -- <data>/settings
DataStorage:getHistoryDir()
DataStorage:getFullDataDir()
```

Put plugin files under `getSettingsDir()` (config) or a subfolder of `getDataDir()` (caches, downloads). Never write into the plugin's own directory — it may be read-only and is wiped on update.

## Plugin-wide settings: LuaSettings

```lua
local LuaSettings = require("luasettings")
local DataStorage = require("datastorage")

function MyPlugin:init()
    self.settings_file = DataStorage:getSettingsDir() .. "/myplugin.lua"
    self.settings = LuaSettings:open(self.settings_file)
    self.timeout = self.settings:readSetting("timeout", 10)       -- 2nd arg = default
end

function MyPlugin:setTimeout(v)
    self.timeout = v
    self.settings:saveSetting("timeout", v)
    self.settings:flush()                                          -- write to disk
end

function MyPlugin:onFlushSettings()
    if self.settings then self.settings:flush() end
end
```

Helpers: `isTrue(key)`, `nilOrTrue(key)`, `toggle(key)`, `flipNilOrTrue(key)`, `delSetting(key)`, `has(key)`. Values may be tables (they are serialized as Lua).

## Global settings: `G_reader_settings`

A global `LuaSettings` for the whole app (`settings.reader.lua`). Use sparingly and namespace keys (`myplugin_foo`) — it's shared with core and every plugin. Reading core values (e.g. `G_reader_settings:readSetting("duration_format")`) is fine.

## Per-book settings

```lua
-- in a reader-only plugin
self.ui.doc_settings:saveSetting("myplugin_position", pos)
local pos = self.ui.doc_settings:readSetting("myplugin_position")
```

Stored in the book's sidecar (`.sdr`/docsettings dir) and flushed by KOReader on close. Module reference: `docsettings`.

## Misc

- JSON: `local JSON = require("json")` (`JSON.encode/decode`); rapidjson is available as `require("rapidjson")`.
- HTTP: `socket.http`/`ssl.https` with `ltn12`, wrapped in `socketutil` (sets timeouts!) — run only inside `NetworkMgr:runWhenOnline`. Always set a timeout: `socketutil:set_timeout(block, total)` … `socketutil:reset_timeout()`.
- Files: `lfs = require("libs/libkoreader-lfs")`, `util = require("util")` (`util.pathExists`, `util.makePath`, `util.splitFilePathName`), `ffiUtil = require("ffi/util")`.
- Time: `os.time()`, `require("ui/time")` for monotonic clock deltas.
