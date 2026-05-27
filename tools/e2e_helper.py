import os

class E2EHelper:
    """Utility class for generating page objects and E2E specs dynamically."""

    @staticmethod
    def ensure_page_object(page_name: str, base_dir: str = "tests/pages") -> str:
        """Create a minimal page‑object file if it does not exist.
        Returns the relative import path (e.g. 'tests/pages/CartPage')."""
        filename = f"{page_name}Page.ts"
        path = os.path.join(base_dir, filename)
        if not os.path.exists(path):
            os.makedirs(base_dir, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(
                    f"import {{ Page }} from '@playwright/test';\n\n"
                    f"export class {page_name}Page {{\n"
                    f"  constructor(private page: Page) {{}}\n\n"
                    f"  async navigate() {{\n"
                    f"    // TODO: add navigation URL for {page_name}\n"
                    f"  }}\n"
                    f"}}\n"
                )
        return f"tests/pages/{page_name}Page"

    @staticmethod
    def build_e2e_spec(flow: list, scope: str, base_url_var: str = "BASE_URL") -> str:
        """Generate the TypeScript content for an end‑to‑end spec.
        * `flow` – ordered list of page names (e.g. ["Login", "Cart", "Checkout"]).
        * `scope` – used in the file name and test title.
        Returns the full spec content as a string."""
        lines = [
            "import { test, expect } from '@playwright/test';",
        ]
        for page in flow:
            lines.append(f"import {{ {page}Page }} from '../pages/{page}Page';")
        lines.append("\n")
        lines.append(f"test.describe('E2E {scope} flow', () => {{")
        lines.append("  let pageObj: any;")
        lines.append("  test.beforeEach(async ({ page }) => {")
        first = flow[0]
        lines.append(f"    pageObj = new {first}Page(page);")
        lines.append("    await pageObj.navigate();")
        lines.append("  });")
        lines.append("\n")
        for idx, page in enumerate(flow):
            if idx > 0:
                lines.append(f"  test('{page} step', async () => {{")
                lines.append(f"    pageObj = new {page}Page(pageObj.page);")
                lines.append("    await pageObj.navigate();")
                lines.append("    // add assertions specific to this page if needed")
                lines.append("  });")
                lines.append("\n")
        lines.append("});")
        return "\n".join(lines)
