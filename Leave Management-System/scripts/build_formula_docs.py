#!/usr/bin/env python3
"""Builds docs/power-fx-formulas.md from the Power Fx source files so that documentation and source cannot drift apart.
Usage: python scripts/build_formula_docs.py          (writes the file)
       python scripts/build_formula_docs.py --check  (exit 1 if the file is out of date)"""
import os, re, sys, yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src", "powerfx")
OUT = os.path.join(ROOT, "docs", "power-fx-formulas.md")


def load(screen):
    return yaml.safe_load(open(os.path.join(SRC, "screens", f"{screen}.fx.yaml"), encoding="utf-8"))


def find(node, name):
    if isinstance(node, dict):
        for k, v in node.items():
            if k.split(" As ")[0] == name:
                return v
            r = find(v, name)
            if r is not None:
                return r
    return None


def formula(screen, control, prop):
    v = find(load(screen), control)
    if v is None or prop not in v:
        raise SystemExit(f"missing {screen}.{control}.{prop}")
    return str(v[prop]).strip()


def pretty(f):
    """Readable multi-line layout for long single-line formulas (display only)."""
    return f


ITEMS = [
    ("1. App start-up", None, None, None,
     "Runs once when the app opens. It identifies the signed-in user in the Dataverse `Users` table, determines whether that user "
     "manages anyone (which controls the *Manager approval* button) and loads this year's leave balance record."),
    ("2. Working-day calculation", "LeaveRequests", "lblDays", "Text",
     "Builds one date for every day between the start and end date, keeps only Monday to Friday (`Weekday(..., StartOfWeek.Monday) < 6`) and counts them. "
     "The result is stored in *Days Requested*."),
    ("3. Request validation message", "LeaveRequests", "lblErr", "Text",
     "A single nested `If` returns the first rule that is broken, or an empty string when the request is valid. The Submit button is disabled while the message is not empty."),
    ("4. Overlap detection", "LeaveRequests", "lblOverlapCount", "Text",
     "Counts the employee's own Pending or Approved requests whose date range intersects the new range (`start <= newEnd` and `end >= newStart`). "
     "A count above zero shows a warning and requires the confirmation check box."),
    ("5. Submit button state", "LeaveRequests", "btnSubmit", "DisplayMode",
     "Disables Submit while validation fails, while a save is running (prevents double submission) or while an overlap has not been acknowledged."),
    ("6. Submit a leave request", "LeaveRequests", "btnSubmit", "OnSelect",
     "Creates the Dataverse row with status Pending, the employee's manager and the calculated days. `Errors()` is checked so a failed save is reported instead of silently ignored."),
    ("7. My requests list", "LeaveRequests", "galMine", "Items",
     "Shows only the signed-in employee's requests, filtered by status and sorted with the newest start date first."),
    ("8. Manager's request list", "ManagerApproval", "galRequests", "Items",
     "Shows requests where the signed-in user is the Manager, never the user's own requests, filtered by the selected status view."),
    ("9. Approve a request and update the balance", "ManagerApproval", "btnApprove", "OnSelect",
     "Re-checks the annual balance, sets the request to Approved with comment and time, and - for Annual leave only - reduces *Annual Leave Balance* and *Remaining Balance* and increases *Total Used*. "
     "If the balance update fails, the approval is reverted to Pending."),
    ("10. Reject button state", "ManagerApproval", "btnReject", "DisplayMode",
     "Rejection is available only when the manager has typed a comment."),
    ("11. Reject a request", "ManagerApproval", "btnReject", "OnSelect",
     "Sets the status to Rejected and stores the comment and decision time. No balance is changed."),
    ("12. Dashboard counters", "ManagerApproval", "lblPendingCount", "Text",
     "Counts the manager's Pending requests; the Approved and Rejected counters use the same pattern with the other status values."),
]


def render():
    out = ["# Power Fx formulas", "",
           "> This page is generated from the files in `src/powerfx/` by `scripts/build_formula_docs.py`; do not edit it by hand.", "",
           "The formulas refer to Dataverse **display names** (for example `'Leave Status'`, `'Days Requested'`). If your tables use different display names, change them in the source files and regenerate this page.", "",
           "| Dataverse object | Display name used in Power Fx |", "|---|---|",
           "| Tables | `'Leave Requests'`, `'Leave Balances'`, `Users` |",
           "| Leave Requests columns | `Employee`, `Manager`, `'Leave Type'`, `'Start Date'`, `'End Date'`, `'Days Requested'`, `Reason`, `'Leave Status'`, `'Manager Comments'`, `'Decision On'`, `'Balance Deducted'` |",
           "| Leave Balances columns | `Employee`, `'Balance Year'`, `'Annual Leave Balance'`, `'Sick Leave Balance'`, `'Other Leave Balance'`, `'Total Used'`, `'Remaining Balance'` |",
           "| Choices | `'LMS Leave Type'` (Annual, Sick, Others), `'LMS Leave Status'` (Pending, Approved, Rejected) |", ""]
    for title, screen, control, prop, text in ITEMS:
        out += [f"## {title}", ""]
        if screen is None:
            body = open(os.path.join(SRC, "App.OnStart.fx"), encoding="utf-8").read().strip()
            out += ["Source: `src/powerfx/App.OnStart.fx` (property `App.OnStart`)", ""]
        else:
            body = formula(screen, control, prop).lstrip("=")
            out += [f"Source: `src/powerfx/screens/{screen}.fx.yaml` - control `{control}`, property `{prop}`", ""]
        out += [text, "", "```text", body, "```", ""]
    return "\n".join(out).rstrip() + "\n"


if __name__ == "__main__":
    text = render()
    if "--check" in sys.argv:
        ok = os.path.exists(OUT) and open(OUT, encoding="utf-8").read() == text
        print("power-fx-formulas.md is up to date" if ok else "power-fx-formulas.md is OUT OF DATE (run scripts/build_formula_docs.py)")
        sys.exit(0 if ok else 1)
    open(OUT, "w", encoding="utf-8").write(text)
    print("written", os.path.relpath(OUT, ROOT))
