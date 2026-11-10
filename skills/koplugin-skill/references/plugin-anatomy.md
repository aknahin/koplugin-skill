# Plugin anatomy and loading

## Layout

```
myplugin.koplugin/
├── _meta.lua      required: fullname + description (shown in Plugin management)
├── main.lua       required: returns the plugin class (or { disabled = true })
├── *.lua          optional helper modules
└── .luacheckrc    optional but recommended (see assets/template.koplugin)
```

- The directory **must end in `.koplugin`**; the loader ignores anything else (`frontend/pluginloader.lua` matches `.+%.koplugin`).
- The loader adds the plugin directory to `package.path`, so sibling modules load with `require("helper")` (keep names distinctive to avoid clashing with core modules, e.g. `myplugin_util.lua`).
- Core plugins ship in `<koreader>/plugins/`. User plugins go in `<koreader data dir>/plugins/` (the loader registers it in the `extra_plugin_paths` setting automatically) — or any directory listed in `extra_plugin_paths` in `settings.reader.lua`.
- A restart of KOReader is required after adding/changing a plugin's `_meta.lua` or after enabling/disabling in Plugin management. Changing only `main.lua` code also needs a restart (modules are cached); in the emulator just relaunch.
- Users can disable plugins via the `plugins_disabled` setting (Tools → More tools → Plugin management). A plugin that returns `{ disabled = true }` from `main.lua` is skipped (this is how `hello.koplugin` ships disabled).

## `_meta.lua`

```lua
local _ = require("gettext")
return {
    fullname = _("Read timer"),
    description = _([[Schedule a reminder after a chosen reading time.]]),
}
```

A `name` field here is deprecated and ignored (loader logs a warning); the plugin id comes from `name` in `main.lua`.

## `main.lua` class

```lua
local MyPlugin = WidgetContainer:extend{
    name = "myplugin",
    is_doc_only = false,
}
```

| Field | Meaning |
|-------|---------|
| `name` | Unique id. Becomes `self.ui.<name>` on the UI object after load, so other plugins/code can reach it (`self.ui.myplugin`). Don't collide with core modules (`self.ui.menu`, `self.ui.document`, `self.ui.view`, `self.ui.statistics` …). |
| `is_doc_only` | `true`: instantiated only inside the reader (a document is open). `false`: also loaded in the file manager, where `self.ui.document` is `nil`. |

`WidgetContainer:extend{}` gives you `self.ui` (the ReaderUI or FileManager instance) automatically when the loader creates the instance with `{ ui = ..., dialog = ... }`.

## Init order

1. `init()` runs when the UI (reader or file manager) is built. Do cheap setup only: read settings, register menu/actions.
2. In the reader, document-dependent work belongs in `onReaderReady()` (document loaded and rendered), or inside `self.ui:registerPostInitCallback(function() ... end)` when you need other plugins to be initialised first (e.g. `self.ui.profiles`, `self.ui.statistics`).
3. `onCloseDocument()` / `onCloseWidget()` for teardown.

## Menu integration

```lua
function MyPlugin:init()
    self.ui.menu:registerToMainMenu(self)     -- makes KOReader call addToMainMenu
end

function MyPlugin:addToMainMenu(menu_items)
    menu_items.myplugin = {                    -- key must be unique across all plugins
        text = _("My plugin"),
        sorting_hint = "more_tools",           -- which top-level tab/submenu
        sub_item_table = {                     -- or `callback = function() ... end`
            { text = _("Do thing"), callback = function() self:doThing() end },
            { text = _("Enabled"),
              checked_func = function() return self.enabled end,
              callback = function() self.enabled = not self.enabled end,
              separator = true },
        },
    }
end
```

`sorting_hint` values commonly used (see `frontend/ui/elements/reader_menu_order.lua` and `filemanager_menu_order.lua`): `tools`, `more_tools`, `setting`, `search`, `navi`, `typeset`, `main`, `filemanager_settings`. Items whose key is not listed in the order tables are appended at the end of that menu. Item fields worth knowing: `text` / `text_func`, `callback`, `sub_item_table` / `sub_item_table_func`, `checked_func`, `enabled_func`, `keep_menu_open`, `separator`, `hold_callback` (long-press), `help_text`.

Dynamic text uses `text_func = function() return T(_("Timeout: %1 s"), self.timeout) end`; call `touchmenu_instance:updateItems()` (callback arg) after changing state when `keep_menu_open = true`.

## Reader-only vs file-manager

- Reader menu hooks are the same API in both; FileManager menu uses `self.ui.menu:registerToMainMenu` too. Check `self.ui.document` before touching book data.
- File manager context adds `self.ui.file_chooser` and, for per-file actions, `self.ui:addFileDialogButtons(id, function(file, is_file, book_props) return {{ text = ..., callback = ... }} end)`.
