# KOReader plugin development

For any task involving KOReader plugins (`*.koplugin`, Lua), read
`skills/koplugin-skill/SKILL.md` first and follow its workflow:

1. Scaffold: `python3 skills/koplugin-skill/scripts/new_plugin.py <id> "<Full Name>"`
2. Implement using `skills/koplugin-skill/references/*.md` as needed
3. Verify: `python3 skills/koplugin-skill/scripts/validate_plugin.py <id>.koplugin`
   and say honestly what was not verified (emulator / device).

Docs: https://koreader.rocks/doc/ · Source: https://github.com/koreader/koreader
