# Drizzle + Hono OpenAPI CRUD generator

Agent skill and Python CLI that scaffold **Drizzle ORM (pg-core)** table definitions with **drizzle-zod**, plus **Hono** `@hono/zod-openapi` CRUD routes, handlers, and router wiring for a fixed TypeScript layout.

## Install the skill

### Option A — Clone into your skills folder

**Project-only** (recommended for a single repo):

```bash
mkdir -p .cursor/skills
git clone git@github.com:brilvio/drizzle-hono-crud-generator-skill.git \
  .cursor/skills/drizzle-hono-crud-generator-skill
```

**Global** (all Cursor projects):

```bash
mkdir -p ~/.cursor/skills
git clone git@github.com:brilvio/drizzle-hono-crud-generator-skill.git \
  ~/.cursor/skills/drizzle-hono-crud-generator-skill
```

Restart Cursor or reload the window so the skill is picked up. The agent reads `SKILL.md` from that folder.

### Option B — Copy this repo

Copy the whole directory (including `SKILL.md`, `scripts/`, `references/`) into `.cursor/skills/drizzle-hono-crud-generator-skill/` or `~/.cursor/skills/drizzle-hono-crud-generator-skill/`.

## How to use it

### With Cursor Agent

Ask the agent to add or regenerate CRUD for a resource (e.g. “scaffold CRUD for `posts` with title and slug”). The skill instructs the agent to run `scripts/generate.py` against your **application root**, not the skill folder.

Your TypeScript app must already match the **required layout** (see [SKILL.md](SKILL.md)): `src/app.ts`, `src/db/schemas/`, `routes/`, and the path aliases expected by the templates (`@/routes/…`, `@/db/schemas/…`, etc.).

### CLI — dependencies

Install Jinja2 once:

```bash
pip install -r /path/to/drizzle-hono-crud-generator-skill/scripts/requirements.txt
# or: uv run --with jinja2 ...
```

### CLI — from your project root

```bash
cd /path/to/your-hono-drizzle-app
python3 /path/to/drizzle-hono-crud-generator-skill/scripts/generate.py posts \
  --field "title:text"
```

### CLI — from anywhere (global skill)

Pass the app root explicitly:

```bash
python3 ~/.cursor/skills/drizzle-hono-crud-generator-skill/scripts/generate.py \
  --root /absolute/path/to/your-app posts \
  --field "slug:varchar:191:y:n"
```

You can also set `DRIZZLE_HONO_CRUD_ROOT` to that absolute path instead of `--root`.

### CLI — more options

- `python3 scripts/generate.py --help` for flags.
- Field syntax and types: [references/drizzle-fields.md](references/drizzle-fields.md).

## What gets generated

| Output | Path (under project root) |
|--------|---------------------------|
| Schema + Zod | `src/db/schemas/{table}.ts` |
| Schema barrel | line appended in `src/db/schemas/index.ts` |
| Routes / handlers / router | `routes/{table}/{table}.routes.ts`, `.handlers.ts`, `.index.ts` |
| App bootstrap | `src/app.ts` — import + `routes` array entry |

## Project layout prerequisites

The generator expects this shape under the root you pass (`--root`, env, or current working directory):

```text
<project-root>/
├── src/
│   ├── app.ts
│   └── db/schemas/
│       └── index.ts
└── routes/
```

Full rules, aliases, and stack assumptions are documented in [SKILL.md](SKILL.md).

## License

See [LICENSE](LICENSE).
