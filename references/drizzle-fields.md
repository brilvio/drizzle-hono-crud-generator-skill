# Drizzle field mapping and Jinja context

## Jinja variables (`scripts/templates/*.jinja`)

| Variable | Meaning |
|----------|---------|
| `Table` | Lowercase table name (TS identifier and filenames). |
| `Capitalized` | First character uppercased (`users` → `Users`). |
| `ImportLine` | `import { …, pgTable } from "drizzle-orm/pg-core";` including field types plus `uuid` and `timestamp`. |
| `Fields` | Column block (excluding fixed `id`, `createdAt`, `updatedAt`). |
| `FieldsSlice` | Field list for conditionals (e.g. `varchar` overrides in insert schema). |
| `has_varchar` | Derived flag for varchar-specific insert schema branch. |

Fixed schema columns: `id` UUID PK with default random; `createdAt` / `updatedAt` timestamps as in `schema.jinja`.

## Drizzle type → column snippet

Emitted order: column expr → optional `.notNull()` → optional `.unique()` → trailing comma.

| Type | Output |
|------|--------|
| uuid | `uuid()` |
| varchar | `varchar({ length: <Length> })` |
| text | `text()` |
| integer | `integer()` |
| bigint | `bigint()` |
| boolean | `boolean()` |
| date | `date()` |
| timestamp | `timestamp({ withTimezone: true })` |
| json | `json()` |
| float | `float()` |
| doublePrecision | `doublePrecision()` |
| serial | `serial()` |
| bigSerial | `bigSerial()` |

`varchar` requires `length`. Other types ignore length.

CLI / JSON defaults: `not_null` defaults **true**; `unique` defaults **false**.
