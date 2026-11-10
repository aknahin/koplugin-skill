--[[--
__FULLNAME__ plugin.

@module koplugin.__CLASS__
--]]--

local Dispatcher = require("dispatcher")
local InfoMessage = require("ui/widget/infomessage")
local LuaSettings = require("luasettings")
local DataStorage = require("datastorage")
local UIManager = require("ui/uimanager")
local WidgetContainer = require("ui/widget/container/widgetcontainer")
local logger = require("logger")
local _ = require("gettext")

local __CLASS__ = WidgetContainer:extend{
    name = "__ID__",
    is_doc_only = false,
}

function __CLASS__:onDispatcherRegisterActions()
    Dispatcher:registerAction("__ID___hello", {
        category = "none",
        event = "__CLASS__Hello",
        title = _("__FULLNAME__: hello"),
        general = true,
    })
end

function __CLASS__:init()
    self.settings = LuaSettings:open(DataStorage:getSettingsDir() .. "/__ID__.lua")
    self.greeting = self.settings:readSetting("greeting", _("Hello from __FULLNAME__"))
    self:onDispatcherRegisterActions()
    self.ui.menu:registerToMainMenu(self)
end

function __CLASS__:addToMainMenu(menu_items)
    menu_items.__ID__ = {
        text = _("__FULLNAME__"),
        sorting_hint = "more_tools",
        callback = function()
            self:on__CLASS__Hello()
        end,
    }
end

function __CLASS__:on__CLASS__Hello()
    logger.dbg("__ID__: hello")
    UIManager:show(InfoMessage:new{ text = self.greeting, timeout = 3 })
    return true
end

function __CLASS__:onFlushSettings()
    if self.settings then
        self.settings:flush()
    end
end

return __CLASS__
