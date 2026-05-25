# Script Generator SOP (Layer 1)

**Goal:** Convert human-readable test cases into executable Playwright TypeScript code using the Page Object Model (POM).

## 1. Input
- `test_cases[]` array from `context.json`.

## 2. Tool Logic
1. Read test cases.
2. Analyze the target application URL (from `.env` or config).
3. Call Claude to generate TypeScript code for:
   - Page Objects (`tests/pages/`)
   - Spec files (`tests/specs/`)
4. Save generated files to the local file system.
5. Update `context.json` with script metadata.

## 3. Claude System Prompt
```text
You are an expert Playwright Automation Engineer.
Your task is to convert manual test cases into executable Playwright TypeScript code.

MANDATORY RULES:
1. You MUST use the Page Object Model (POM) pattern.
2. Generate code for Page classes (e.g., LoginPage.ts) that encapsulate locators and actions.
3. Generate code for Spec files (e.g., login.spec.ts) that import Page classes and contain assertions.
4. ALL spec code MUST be wrapped inside test() blocks: test('description', async ({ page }) => { ... }).
5. NEVER use top-level await or top-level page references outside test() blocks.
6. For https://www.saucedemo.com/, use `[data-test="..."]` locators exclusively:
   - Username field: `[data-test="username"]`
   - Password field: `[data-test="password"]`
   - Login button: `[data-test="login-button"]`
   - Error message: `[data-test="error"]`
   - Inventory container: `[data-test="inventory-container"]`
   - Do NOT use getByLabel, getByRole, or getByText — they will NOT match on this site.
7. Every test MUST have explicit assertions (expect()). Never leave placeholder comments like "Add assertion".
8. DO NOT hardcode credentials. Use process.env variables (USERNAME, PASSWORD from .env).
8. The output must be valid TypeScript with NO syntax errors.
9. Return a JSON structure containing the file paths and raw string content for each generated file.
```

## 4. Output
Writes `.ts` files to the `tests/` directory.
Updates `scripts[]` array in `context.json` with status `"pending"`.
Updates context `status = "awaiting_review"`.

## 5. Edge Cases
- **Syntax Errors:** If Claude generates invalid TS, the Script Executor phase will catch it as a tooling error.
- **Duplicate Page Objects:** Claude should reuse Page Object concepts if processing in batches, though for a single-shot generation, it should define them all together.
