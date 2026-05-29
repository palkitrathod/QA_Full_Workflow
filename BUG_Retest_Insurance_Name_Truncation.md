# Bug Retest — QA Requirements & Test Specification

**DME Rocket | Insurance Name Truncation Fix Validation**
Version 1.0 | Platform: dev.dmerocket.com

---

## 1. Document Information

| Field | Details |
|---|---|
| Document Title | Insurance Name Truncation — Bug Retest Requirements & Test Specification |
| Project / Module | DME Rocket — App Config / Insurance Module |
| Bug Summary | Insurance name being truncated on save; full name not persisted or displayed |
| Base URL | https://dev.dmerocket.com/insurance |
| Version | 1.0 |
| Prepared For | QA / Automation Engineering Team |
| User Type | Authenticated Admin |
| Scope | Create Insurance → Edit Insurance → Insurance Listing Page |

---

## 2. Objective

This document defines the retest requirements and test cases to validate the fix for the insurance name truncation bug on the DME Rocket platform. The bug caused long insurance names entered in the "Name" field to be cut short during both create and update operations.

The fix must be validated across:

- Add (Create) insurance screen
- Edit (Update) insurance screen
- Insurance listing page — to confirm the full name reflects in the UI after save

---

## 3. Bug Details

| Field | Details |
|---|---|
| Bug Type | Data truncation on save |
| Affected Field | Name (Insurance) |
| Affected Operations | Create, Update |
| Affected Screens | Add Insurance form, Edit Insurance form, Insurance listing page |
| Example Input | `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL)` |
| Incorrect Saved Value | `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEV)` |
| Expected Saved Value | `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL)` |
| Root Cause (Reported) | Name field character limit was insufficient to hold the full string |
| Fix Status | Resolved by development team — pending QA retest |

---

## 4. Test Credentials

| Field | Value |
|---|---|
| Application URL | https://dev.dmerocket.com/insurance |
| Username | admin@selectortho.net |
| Password | Password123! |
| Role | Admin |

---

## 5. Test Data

| Field | Value | Notes |
|---|---|---|
| Full Insurance Name | BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL) | 52-character string; was previously truncated to 50 chars |
| Truncated (Buggy) Value | BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEV) | Should NOT appear after fix |
| Short Insurance Name | TEST INSURANCE SHORT | Control value; must also save correctly |
| Updated Insurance Name | BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL) UPDATED | Extended name for edit retest |

---

## 6. Functional Requirements

### 6.1 Application Access & Navigation

- **FR-001:** The application shall load successfully at https://dev.dmerocket.com/insurance with a valid login.
- **FR-002:** Admin user shall be able to log in using the provided credentials.
- **FR-003:** After login, the top menu bar shall display the "App Config" menu item.
- **FR-004:** Navigating to App Config → Insurance shall load the Insurance listing page.

### 6.2 Insurance Name Field — Character Capacity

- **FR-005:** The "Name" field on the Add Insurance form shall accept and persist the full value `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL)` without truncation.
- **FR-006:** The "Name" field on the Edit Insurance form shall accept and persist updated long name values without truncation.
- **FR-007:** The Name field shall support a minimum of 100 characters without truncation.
- **FR-008:** The Name field shall not silently truncate input; if a limit exists it shall display an explicit validation message.

### 6.3 Create (Add) Insurance

- **FR-009:** The Add Insurance form shall be accessible from the Insurance listing page.
- **FR-010:** The user shall be able to enter a long insurance name (52+ characters) into the Name field.
- **FR-011:** On clicking Save / Submit, the full name shall be persisted to the database without truncation.
- **FR-012:** After saving, the user shall be redirected to or shown the Insurance listing page.
- **FR-013:** The newly created insurance record shall appear in the listing with the full, untruncated name.

### 6.4 Edit (Update) Insurance

- **FR-014:** An existing insurance record shall be editable from the listing page.
- **FR-015:** The Edit form shall pre-populate the Name field with the currently saved full name.
- **FR-016:** The user shall be able to modify the Name field to a long value and save successfully.
- **FR-017:** After saving the edit, the updated full name shall be persisted without truncation.
- **FR-018:** The updated name shall reflect correctly on the Insurance listing page after edit.

### 6.5 Insurance Listing Page

- **FR-019:** The Insurance listing page shall display the full insurance name for all records.
- **FR-020:** Long names shall not be clipped, hidden, or truncated in the listing UI without a visible indicator (e.g. tooltip or expand).
- **FR-021:** The listing page shall correctly reflect any create or update operation immediately after save.

---

## 7. Test Scenarios

| ID | Scenario Name | Description |
|---|---|---|
| TS-001 | Login & Navigation | Verify admin can log in and navigate to the Insurance section via App Config |
| TS-002 | Create Insurance with Long Name | Verify full name is accepted and saved without truncation on Add screen |
| TS-003 | Verify Listing After Create | Verify the full name appears correctly on the Insurance listing page after creation |
| TS-004 | Edit Insurance with Long Name | Verify full name is accepted and saved without truncation on Edit screen |
| TS-005 | Verify Listing After Edit | Verify the updated full name appears correctly on the listing page after edit |
| TS-006 | Boundary & Negative Tests | Verify behaviour with names at/above previous truncation threshold and with short names |

---

## 8. Detailed Test Cases

### TS-001 — Login & Navigation

| TC ID | Title | Steps | Expected Result | Priority |
|---|---|---|---|---|
| TC-001 | Valid admin login | Navigate to https://dev.dmerocket.com/insurance; Enter username `admin@selectortho.net` and password `Password123!`; Click Login | User is authenticated and lands on the application dashboard | High |
| TC-002 | Navigate to Insurance section | After login, click "App Config" from the top menu bar; Select "Insurance" | Insurance listing page loads successfully | High |

### TS-002 — Create Insurance with Long Name

| TC ID | Title | Steps | Expected Result | Priority |
|---|---|---|---|---|
| TC-003 | Open Add Insurance form | On Insurance listing page, click Add / New Insurance button | Add Insurance form is displayed with empty fields | High |
| TC-004 | Enter full long name on create | In the Name field enter `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL)`; Fill any other required fields; Click Save | Form submits without error; no truncation error message | Critical |
| TC-005 | Verify saved name on create | After save, open the newly created record or observe the listing | Name saved is exactly `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL)` — not `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEV)` | Critical |

### TS-003 — Verify Listing After Create

| TC ID | Title | Steps | Expected Result | Priority |
|---|---|---|---|---|
| TC-006 | Full name visible in listing | After creating the record (TC-004), navigate to Insurance listing page | The record appears with the full name `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL)` displayed | Critical |
| TC-007 | No truncation in listing UI | Observe the Name column for the newly created record | Name is not cut short or hidden in the listing; full value is visible or accessible | High |

### TS-004 — Edit Insurance with Long Name

| TC ID | Title | Steps | Expected Result | Priority |
|---|---|---|---|---|
| TC-008 | Open Edit form for existing record | On Insurance listing page, click Edit on an existing insurance record | Edit Insurance form opens with current name pre-populated | High |
| TC-009 | Verify pre-populated name is full | Observe the Name field on the Edit form | If the record was previously saved with the full name, the Name field shows the full untruncated value | High |
| TC-010 | Update name to long value and save | Clear the Name field; Enter `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL) UPDATED`; Click Save | Form submits without error; updated name is persisted in full | Critical |
| TC-011 | Verify updated name after edit | After saving, open the record again or observe listing | Name reflects `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEVEL) UPDATED` exactly | Critical |

### TS-005 — Verify Listing After Edit

| TC ID | Title | Steps | Expected Result | Priority |
|---|---|---|---|---|
| TC-012 | Updated full name visible in listing | After editing (TC-010), navigate to Insurance listing page | The updated full name is displayed correctly in the listing | Critical |
| TC-013 | No truncation after edit in listing | Observe the Name column for the edited record | Name is not cut short; full updated value is visible | High |

### TS-006 — Boundary & Negative Tests

| TC ID | Title | Steps | Expected Result | Priority |
|---|---|---|---|---|
| TC-014 | Name at previous truncation threshold | Enter a name of exactly 50 characters (the old cutoff); Save | Name saves and displays in full; no truncation at 50-char boundary | High |
| TC-015 | Name just above previous threshold | Enter a name of 51+ characters; Save | Name saves and displays in full; fix is confirmed beyond old limit | Critical |
| TC-016 | Short name still saves correctly | Enter a short name e.g. `TEST INSURANCE SHORT`; Save | Short name saves and displays without any regression | Medium |
| TC-017 | Name field with special characters | Enter `BCBS TPA (MID-LEVEL) & ASSOCIATES — SOUTHWEST`; Save | Special characters preserved; name not truncated or altered | Medium |

---

## 9. Acceptance Criteria

The bug fix is considered verified and the feature accepted when ALL of the following conditions are met:

- TC-004 and TC-005 pass — long name saves and persists correctly on Create.
- TC-010 and TC-011 pass — long name saves and persists correctly on Edit.
- TC-006 and TC-012 pass — full name displays correctly on the Insurance listing page after both Create and Edit.
- TC-015 passes — names beyond the previous 50-character truncation threshold are now saved in full.
- No regression observed for short names (TC-016).
- The previously truncated value `BCBS TPA SOUTHWEST SERVICE ADMINISTRATORS (MID-LEV)` does not appear anywhere after saving the full name.

---

## 10. Revision History

| Version | Date | Description | Author |
|---|---|---|---|
| 1.0 | 2026-05-28 | Initial retest specification for insurance name truncation bug fix | QA Team |
