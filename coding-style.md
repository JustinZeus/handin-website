# Coding Style Rules

## Python (Backend)

### General

- Python 3.12+ features encouraged (type parameter syntax, match statements where clearer).
- `ruff` handles formatting and linting. Config lives in `pyproject.toml`.
- `mypy` in strict mode. No `Any` types. No `# type: ignore` without a comment explaining why.

### Naming

| Entity | Convention | Example |
|---|---|---|
| Files/modules | `snake_case` | `order_service.py` |
| Functions | `snake_case` | `calculate_total()` |
| Classes | `PascalCase` | `Invoice` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| Database columns | `snake_case` | `created_at` |
| Pydantic models | `PascalCase` + suffix | `ItemCreateRequest`, `ItemResponse` |

### Functions

- Max 50 lines. If longer, extract helpers.
- Use early returns to avoid nesting (see Negative Space Programming below).

### Negative Space Programming (Fail Early)

Reject invalid state at the top of every function. The happy path is the code that
remains after all guard clauses. This applies at every layer.

**Guard clauses before logic:**

```python
# CORRECT - fail early, happy path is clean
def process_order(quantity: int, unit_price: Decimal) -> OrderResult:
    if quantity <= 0:
        raise ValidationError("Quantity must be positive")
    if unit_price <= 0:
        raise ValidationError("Unit price must be positive")

    total = quantity * unit_price
    return OrderResult(total=total)

# WRONG - nested conditionals, happy path buried
def process_order(quantity: int, unit_price: Decimal) -> OrderResult:
    if quantity > 0:
        if unit_price > 0:
            total = quantity * unit_price
            return OrderResult(total=total)
        else:
            raise ValidationError("Unit price must be positive")
    else:
        raise ValidationError("Quantity must be positive")
```

**Key rules:**
- Max 3 levels of indentation in any function. If deeper, extract or flatten.
- Never use `else` after a `return`, `raise`, or `throw` — the guard already exited.
- No silent failures: if something is wrong, raise/throw immediately with context.
- Optional/nullable returns are acceptable only when "not found" is a normal case (e.g., repository lookups). For business rule violations, always raise.

### Imports

- Group: stdlib -> third-party -> local. Ruff enforces this.
- No wildcard imports (`from module import *`).
- No relative imports across packages. Use absolute imports: `from app.module import ...`.

### Type Hints

- All function signatures must have type hints (params and return).
- Use `UUID` from `uuid`, not `str`, for ID fields.
- Use `datetime` from `datetime`, not `str`, for timestamps.
- Collections: `list[Item]`, not `List[Item]` (Python 3.12+).

## TypeScript (Frontend)

### General

- Strict TypeScript. No `any`. No `@ts-ignore` without explanation.
- ESLint + Prettier via the project config. No overrides in individual files.

### Naming

| Entity | Convention | Example |
|---|---|---|
| Files (components) | `PascalCase.vue` | `OrderForm.vue` |
| Files (composables) | `camelCase.ts` | `useOrderForm.ts` |
| Files (utilities) | `camelCase.ts` | `formatCurrency.ts` |
| Variables/functions | `camelCase` | `calculateTotal()` |
| Types/interfaces | `PascalCase` | `Order` |
| Constants | `UPPER_SNAKE_CASE` | `DEFAULT_PAGE_SIZE` |
| Props | `camelCase` | `orderItems` |
| Events | `camelCase` verb | `@submit`, `@update:modelValue` |

### Vue Components

- Use `<script setup lang="ts">` exclusively. No Options API.
- Props and emits must be typed with `defineProps<{}>()` and `defineEmits<{}>()`.
- One component per file. Max 400 lines target.
- Composables for reusable stateful logic. Components for reusable UI.

### No Default Exports (except Vue components)

```typescript
// CORRECT
export function calculateTotal(...) { ... }
export interface Order { ... }

// WRONG
export default function calculateTotal(...) { ... }
```

Vue components are the exception (required by Vue conventions).

## Shared Rules

### Dependencies

- Do not add dependencies without discussing first. Check if stdlib or an existing dep solves it.
- Pin exact versions in `pyproject.toml` and `package.json`.

### Comments

- Code should be self-documenting. Comments explain WHY, not WHAT.
- No commented-out code. Use git history.
- Docstrings on public functions in the domain layer (they're the API for other layers).

### File Organization

- No barrel files (`__init__.py` re-exports or `index.ts` re-exports). Import directly.
- No "utils" grab-bag files. If a utility is specific to a domain, put it in that domain's directory.
- If a file exceeds 600 lines, it must be split before adding more code.
