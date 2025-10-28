# GEMINI.md - TTB Label Verification System

> **Project Context for Gemini**
>
> This document contains the rules and guidelines I will follow when working on this codebase. It is derived from `CLAUDE.md` and serves as my operational standard.

---

## 1. My Core Directives

1.  **Primary Goal:** Assist in developing the TTB Label Verification System, an AI-powered tool to pre-check alcohol labels against TTB regulations.
2.  **Source of Truth:** I will prioritize information and requirements in the following order:
    1.  `docs/prd.md` (Product Requirements Document)
    2.  `docs/regulatoryrequirements.md` (TTB Rules)
    3.  `CLAUDE.md` (Project standards for AI assistants)
    4.  Existing code patterns and conventions.
3.  **Simplicity and Scope:** I will focus on delivering a functional MVP. I understand this is a pre-check tool, not an official TTB certification service.
4.  **Security First:** I will never commit secrets, API keys, or environment files (`.env*`, `service-account.json`). I will sanitize all inputs and validate file types.

---

## 2. Technology & Code Style

### **Frontend (Next.js / TypeScript)**

-   **Framework/Language:** Next.js 14 (App Router) with TypeScript 5.x (strict mode).
-   **Styling:** Tailwind CSS.
-   **State & Forms:** React Hook Form with Zod for validation.
-   **Naming Conventions:**
    -   Components: `PascalCase` (e.g., `LabelForm`).
    -   Functions/Variables: `camelCase` (e.g., `validateField`).
    -   Interfaces: `PascalCase` (e.g., `LabelFormData`).
    -   Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_FILE_SIZE`).
-   **Best Practices:** I will use `async/await`, prefer `interface` for objects, and add JSDoc comments to complex logic.

### **Backend (Python / Firebase)**

-   **Runtime/Language:** Firebase Cloud Functions (2nd gen) with Python 3.11.
-   **Package Management:** I will **exclusively** use `uv`. I will **never** use `pip` or `poetry` directly for package installation.
    -   **To install a package:** `uv pip install <package-name>`
    -   **To update requirements:** `uv pip compile pyproject.toml -o requirements.txt`
-   **Naming Conventions:**
    -   Functions/Variables: `snake_case` (e.g., `verify_label`).
    -   Classes: `PascalCase` (e.g., `FormData`).
    -   Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_IMAGE_SIZE`).
-   **Best Practices:** I will use type hints, Python 3.11+ features, dataclasses for data structures, and Google-style docstrings.

---

## 3. Critical Verification Logic

I will adhere to the following specific rules when implementing verification logic:

-   **Out of Scope:** I will **not** attempt to verify requirements that are technically infeasible with OCR. This includes:
    -   ❌ Spatial layout ("Same Field of Vision").
    -   ❌ Font styling (bold, italics).
    -   ❌ Font sizes.
    -   ❌ Color requirements.
    I will explain these limitations if asked to implement such features.

-   **Government Warning:** I will implement this check using a **95% fuzzy match** to tolerate minor OCR errors. I will verify:
    -   "GOVERNMENT WARNING" is in all caps.
    -   "Surgeon General" is correctly capitalized.
    -   The presence of keywords related to pregnancy, birth defects, and driving/machinery impairment.

-   **Conditional Requirements:** I will only enforce these fields based on the specified conditions:
    -   **Age Statement:** Only for whisky < 4 years or brandy < 2 years.
    -   **Country of Origin:** Only if `is_imported` is true.
    -   **Sulfite Declaration:** Only if `contains_sulfites` is true.

-   **Standards of Fill:** I will check net contents against the approved list (50ml, 100ml, etc.) and issue a **warning** for non-standard sizes, not a failure.

---

## 4. Common Workflows

### **Adding a New Form Field**

1.  **Type Update:** Add the field to the `LabelFormData` interface in `frontend/src/types/index.ts`.
2.  **Model Update:** Add the field to the `FormData` dataclass in `functions/models.py`.
3.  **UI Update:** Add the input element to the form in `frontend/src/components/LabelForm.tsx`.
4.  **Logic Update:** Implement the corresponding check in `functions/verification.py`.
5.  **Docs Check:** I will ask if the PRD needs to be updated.

### **Deploying Changes**

-   I will use the `firebase deploy` command.
-   For backend changes, I will first run `uv pip compile pyproject.toml -o requirements.txt` from the `functions` directory.

### **Testing**

-   I will write unit tests for new backend logic using `pytest`.
-   I will write unit tests for new frontend logic using Jest and React Testing Library.
-   I will use `docs/sample-labels/` for manual test cases.

---
This document serves as my guide. I will refer to it to ensure my work is consistent, accurate, and aligned with the project's goals.
