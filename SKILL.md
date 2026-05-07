---
name: drizzle-hono-crud-generator-skill
description: Runs or extends the bundled Python CLI in scripts/generate.py to scaffold Drizzle ORM (pg-core) table schemas with drizzle-zod, plus Hono Zod OpenAPI CRUD routes, handlers, and router wiring. Requires a fixed TypeScript project layout (src/app.ts, src/db/schemas, routes/). Project root comes from --root, DRIZZLE_HONO_CRUD_ROOT, or cwd — never by walking up from the skill install path. Use when adding CRUD resources or maintaining the generator across global or project-local skill installs.
---

# Drizzle + Hono OpenAPI CRUD generator

## Required project layout

The generator writes paths relative to the **project root** (`--root`, env, or `cwd`). The repo **must** match this shape (names are fixed in `scripts/generate.py` and in the Jinja templates):

```text
<project-root>/
├── src/
│   ├── app.ts                      # MUST exist — patched for default route import + `const routes = [...]`
│   └── db/
│       └── schemas/
│           ├── index.ts            # Barrel — new `export * from "./{table}";` lines appended
│           └── {table}.ts          # CREATED — Drizzle table + Zod insert/select/patch schemas
└── routes/
    └── {table}/
        ├── {table}.routes.ts       # CREATED — @hono/zod-openapi route defs
        ├── {table}.handlers.ts     # CREATED — DB access handlers
        └── {table}.index.ts        # CREATED — default-export router wiring
```

**Hard requirements**

- **`src/`** and **`routes/`** exist directly under the project root (the CLI validates both).
- **`src/app.ts`** exists and contains **`const app = createApp()`** (or at least the substring **`const app =`**) and a **`const routes = [`** array the tool can prepend entries into.
- **Path aliases** in `tsconfig`/bundler must resolve the imports emitted by templates, including `@/routes/…`, `@/db/schemas/…`, `@/db`, `@/lib/create-app`, `@/lib/types`, `@/lib/consts`. Adjust templates under `scripts/templates/` if your aliases differ.
- **Runtime stack** assumed by templates: Hono with `@hono/zod-openapi`, `drizzle-orm`, `drizzle-zod`, `zod`, and the same helper imports as in the shipped `.jinja` files (e.g. `stoker/*` patterns). Fork templates if your stack differs.

## Bundled skill layout

```text
drizzle-hono-crud-generator-skill/
├── SKILL.md
├── scripts/
│   ├── generate.py
│   ├── requirements.txt        # jinja2
│   └── templates/*.jinja
└── references/
    └── drizzle-fields.md
```

Install location can be **project** (`.cursor/skills/…`) or **global** (`~/.cursor/skills/…`). The script never infers the project root from its own file path.

## Resolving the project root

1. **`--root /absolute/path/to/project`**
2. **`DRIZZLE_HONO_CRUD_ROOT`** environment variable
3. **`cwd`** when invoking Python

Then the tool checks that **`src/`** and **`routes/`** exist under that root.

## Running the CLI

Install **Jinja2** once (`pip install -r scripts/requirements.txt` or `uv run --with jinja2`).

From the project root (`cwd` correct):

```bash
python3 /path/to/drizzle-hono-crud-generator-skill/scripts/generate.py posts \
  --field "title:text"
```

From elsewhere (e.g. global skill):

```bash
python3 ~/.cursor/skills/drizzle-hono-crud-generator-skill/scripts/generate.py \
  --root /absolute/path/to/project posts --field "slug:varchar:191:y:n"
```

**Agent rule:** prefer executing `scripts/generate.py`; pass **`--root`** when the shell cwd is not the project root.

CLI details: `--help`, `--field`, `--spec` JSON. Field types and template variables: [references/drizzle-fields.md](references/drizzle-fields.md).

## Generated artifacts

| Output | Path (relative to project root) |
|--------|----------------------------------|
| Schema + Zod | `src/db/schemas/{table}.ts` |
| Schema barrel | append line to `src/db/schemas/index.ts` |
| Routes / handlers / router | `routes/{table}/{table}.routes.ts`, `.handlers.ts`, `.index.ts` |
| App bootstrap | `src/app.ts` — default import `@/routes/{table}/{table}.index` + `routes` array entry |
