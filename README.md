# koplugin-skill

An [Agent Skill](https://agentskills.io) that teaches AI coding agents (Claude Code, Codex CLI, Gemini CLI, OpenCode, Cursor, …) to **build, review, debug and verify [KOReader](https://github.com/koreader/koreader) plugins**.

It bundles condensed knowledge from the official docs ([koreader.rocks/doc](https://koreader.rocks/doc/), [Development guide](https://koreader.rocks/doc/topics/Development_guide.md.html)) and KOReader's own source, plus tooling:

| Piece | What it does |
|-------|--------------|
| `SKILL.md` | Workflow, minimal plugin, rules and the "why" behind them |
| `references/` | Plugin anatomy, widgets, events/Dispatcher, settings, testing & device install, pitfalls |
| `scripts/new_plugin.py` | Scaffolds a working `<id>.koplugin` (menu, Dispatcher action, settings) |
| `scripts/validate_plugin.py` | Static verification: structure, `_meta.lua`, menu/Dispatcher wiring, gettext, LuaJIT syntax, luacheck |
| `assets/template.koplugin/` | The template, with a KOReader-compatible `.luacheckrc` |

## Install

Runs straight from GitHub (no npm publish needed):

```bash
npx github:aknahin/koplugin-skill                      # Claude Code -> ~/.claude/skills
npx github:aknahin/koplugin-skill install --all        # every supported agent
```

Once published to npm the short form `npx koplugin-skill` is equivalent. Options:

```bash
# Claude Code (default, to ~/.claude/skills)
npx koplugin-skill

# other agents / scopes
npx koplugin-skill install --agent codex,gemini
npx koplugin-skill install --all
npx koplugin-skill install --project            # into ./.claude/skills of the current repo
npx koplugin-skill install --dir ~/my/skills    # any SKILL.md-aware agent
npx koplugin-skill uninstall
```

No npm? Use git directly:

```bash
git clone https://github.com/aknahin/koplugin-skill.git
cp -R koplugin-skill/skills/koplugin-skill ~/.claude/skills/
```

Agents without skill support can read [`AGENTS.md`](AGENTS.md), which points to the same files.

## Use

Ask your agent things like:

- "Create a KOReader plugin that shows my reading streak in the Tools menu"
- "Why doesn't my koplugin appear in Plugin management on my Kobo?"
- "Review this main.lua for KOReader best practices"

Run the tools yourself (Python 3, no dependencies):

```bash
python3 skills/koplugin-skill/scripts/new_plugin.py readstreak "Read Streak" --dir .
python3 skills/koplugin-skill/scripts/validate_plugin.py readstreak.koplugin
```

Optional but recommended for deeper checks: `luajit` and `luacheck` (`brew install luajit luacheck`). Static checks cannot replace running the plugin in the KOReader emulator (`./kodev run`) or on a device — the skill tells the agent to report exactly what was and wasn't verified.

## Develop

```bash
npm test          # installer test
```

PRs welcome — especially corrections against newer KOReader releases.

## License

MIT
