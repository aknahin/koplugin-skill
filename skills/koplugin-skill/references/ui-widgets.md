# UI widgets cheat-sheet

All widgets are created with `Widget:new{...}` and displayed via `UIManager:show(w)`; remove with `UIManager:close(w)`. Full API per widget: `https://koreader.rocks/doc/modules/ui.widget.<name>.html`. Verify argument names there — they occasionally change.

```lua
local UIManager = require("ui/uimanager")
local _ = require("gettext")
local T = require("ffi/util").template
```

## Messages

```lua
local InfoMessage = require("ui/widget/infomessage")
UIManager:show(InfoMessage:new{ text = _("Saved"), timeout = 2 })   -- auto-dismiss

local Notification = require("ui/widget/notification")
Notification:notify(_("Timer started"))      -- unobtrusive toast, no tap needed
```

## Confirm

```lua
local ConfirmBox = require("ui/widget/confirmbox")
UIManager:show(ConfirmBox:new{
    text = _("Delete all entries?"),
    ok_text = _("Delete"),
    ok_callback = function() self:clear() end,
})
```

## Text input

```lua
local InputDialog = require("ui/widget/inputdialog")
local dlg
dlg = InputDialog:new{
    title = _("Server URL"),
    input = self.settings.url or "",
    input_hint = "https://…",
    buttons = {{
        { text = _("Cancel"), id = "close", callback = function() UIManager:close(dlg) end },
        { text = _("Save"), is_enter_default = true, callback = function()
            self.settings.url = dlg:getInputText()
            UIManager:close(dlg)
        end },
    }},
}
UIManager:show(dlg)
dlg:onShowKeyboard()
```

Multiple fields: `ui/widget/multiinputdialog` with `fields = {{ text = "", hint = _("…") }, …}` and `MultiInputDialog:getFields()`.

## Numbers and dates

```lua
local SpinWidget = require("ui/widget/spinwidget")
UIManager:show(SpinWidget:new{
    title_text = _("Minutes"), value = 10, value_min = 1, value_max = 120, value_step = 1,
    callback = function(spin) self.minutes = spin.value end,
})
```
Also: `doublespinwidget`, `datetimewidget`, `timewidget`.

## Lists and menus

```lua
local Menu = require("ui/widget/menu")
local Screen = require("device").screen
local menu
menu = Menu:new{
    title = _("Pick one"),
    item_table = {
        { text = "Alpha", callback = function() UIManager:close(menu); self:pick("a") end },
        { text = "Beta",  mandatory = "3", callback = function() … end },  -- mandatory = right-aligned text
    },
    width = Screen:getWidth(), height = Screen:getHeight(),
    covers_fullscreen = true,
    is_borderless = true, is_popout = false,
}
UIManager:show(menu)
```
Simple choice popups: `ui/widget/buttondialog` (`buttons = {{ {text=…, callback=…} }}`) — usually better than `Menu` for ≤6 options. Key/value info pages: `ui/widget/keyvaluepage`. Read-only long text: `ui/widget/textviewer`. File/folder picking: `ui/widget/pathchooser`.

## Long operations and progress

```lua
local Trapper = require("ui/trapper")
Trapper:wrap(function()
    Trapper:info(_("Working…"))                       -- progress message
    local completed, result = Trapper:dismissableRunInSubprocess(function()
        return heavy_work()                           -- runs in a forked process
    end, trapper_widget_or_true)
    if not completed then return end                  -- user tapped to cancel
    Trapper:reset()
end)
```

Network:

```lua
local NetworkMgr = require("ui/network/manager")
NetworkMgr:runWhenOnline(function() self:sync() end)   -- prompts WiFi on if needed
```

## Widget lifecycle tips

- Each widget you show should be closed by you (or dismiss itself). Keep a reference if you need to close it from a callback.
- Implement `onCloseWidget` on custom widgets to unschedule timers.
- Prefer composing existing widgets over building custom `InputContainer`s; if you need a custom layout, prototype it with `./kodev wbuilder`.
- Screen metrics: `local Screen = require("device").screen`; use `Screen:scaleBySize(n)` for sizes so they scale with DPI, `Size.padding.default` etc. from `ui/size`.
