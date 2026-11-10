unused_args = false
std = "luajit"
-- ignore implicit self
self = false

globals = {
    "G_reader_settings",
    "G_defaults",
    "table.pack",
    "table.unpack",
}

read_globals = {
    "_ENV",
}

ignore = {
    "211/__*", -- Unused local variable
    "231/__",  -- Local variable is set but never accessed
    "631",     -- Line is too long
}
