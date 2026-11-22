#!/usr/bin/env python3
"""Offline repository checks (no Power Platform environment needed). Exit code 1 when an ERROR is found.
 1 YAML of Power Fx screens parses        2 Python compiles          3 sample data is consistent
 4 docs use only columns that the schema script creates               5 Power Fx identifiers match schema display names
 6 generated formula document is current  7 file references/links resolve   8 forbidden headings absent"""
import ast, csv, datetime as dt, glob, os, re, subprocess, sys
try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
errors, warns = [], []
def err(m): errors.append(m)
def rel(p): return os.path.relpath(p, ROOT)
def read(p): return open(os.path.join(ROOT, p), encoding="utf-8").read()
def files(pattern): return glob.glob(os.path.join(ROOT, pattern), recursive=True)

# 1, 2
for f in files("src/powerfx/screens/*.yaml"):
    try: yaml.safe_load(open(f, encoding="utf-8"))
    except Exception as e: err(f"YAML invalid {rel(f)}: {str(e).splitlines()[0]}")
for f in files("dataverse/*.py") + files("scripts/*.py"):
    try: ast.parse(open(f, encoding="utf-8").read())
    except SyntaxError as e: err(f"Python syntax {rel(f)}: {e}")

# schema facts
schema = read("dataverse/create_schema.py")
cols = re.findall(r'\bc_(?:pick|date|datetime|int|memo|str|bool|lookup)\(\s*\w+,\s*f"\{P\}_(\w+)",\s*"([^"]+)"', schema)
known = {c.lower() for c, _ in cols}
display = {d for _, d in cols}
for sch, disp, plural, prim, pdisp in re.findall(r'table\(f"\{P\}_(\w+)",\s*"([^"]+)",\s*"([^"]+)",\s*f"\{P\}_(\w+)",\s*"([^"]+)"\)', schema):
    known |= {sch.lower(), prim.lower()}; display |= {disp, plural, pdisp}
choice_labels = set()
for n, d, labels in re.findall(r'f"\{P\}_(\w+)":\s*\("([^"]+)",\s*\[([^\]]+)\]', schema):
    known.add(n.lower()); display.add(d); choice_labels |= set(re.findall(r'"([^"]+)"', labels))
display |= choice_labels
if len(cols) != 18: err(f"schema defines {len(cols)} custom columns, expected 18 (11 Leave Requests + 7 Leave Balances)")
extra_ok = {"leaverequestid", "leavebalanceid", "leaverequests", "leavebalances", "leaverequest", "leavebalance"}

# 4 docs/readme use <prefix>_name
for f in files("docs/*.md") + files("README.md"):
    for tok in set(re.findall(r"<prefix>_([A-Za-z]+)", open(f, encoding="utf-8").read())):
        t = tok.lower()
        if t not in known and t not in extra_ok: err(f"unknown column '<prefix>_{tok}' in {rel(f)}")

# 5 Power Fx identifiers
sysnames = {"Leave Requests", "Leave Balances", "Users", "Primary Email", "Full Name", "Employee", "Manager"}
for f in files("src/powerfx/**/*.fx*"):
    txt = re.sub(r'"[^"\n]*"', '""', open(f, encoding="utf-8").read())
    for ident in set(re.findall(r"'([^'\n]+)'", txt)):
        if ident not in display and ident not in sysnames: err(f"Power Fx identifier '{ident}' in {rel(f)} is not a schema display name")

# 3 sample data
users = list(csv.DictReader(open(os.path.join(ROOT, "sample-data/sample_users.csv"), encoding="utf-8")))
reqs = list(csv.DictReader(open(os.path.join(ROOT, "sample-data/sample_requests.csv"), encoding="utf-8")))
emails = {u["email"] for u in users}; mgr = {u["email"]: u["manager_email"] for u in users}
for u in users:
    seen, cur = set(), u["email"]
    while cur:
        if cur in seen: err(f"manager cycle at {cur}"); break
        seen.add(cur); cur = mgr.get(cur, "")
    if u["manager_email"] and u["manager_email"] not in emails: err(f"unknown manager {u['manager_email']}")
def wd(s, e):
    s, e = dt.date.fromisoformat(s), dt.date.fromisoformat(e)
    return sum(1 for i in range((e - s).days + 1) if (s + dt.timedelta(i)).weekday() < 5)
used = {e: 0 for e in emails}
for r in reqs:
    if r["employee_email"] not in emails: err(f"request for unknown user {r['employee_email']}"); continue
    if int(r["days"]) != wd(r["start"], r["end"]): err(f"days mismatch {r['employee_email']} {r['start']}")
    if r["status"] == "Rejected" and not r["comments"].strip(): err(f"rejected request without comment: {r['start']}")
    if r["status"] == "Approved" and r["type"] == "Annual": used[r["employee_email"]] += int(r["days"])
for u in users:
    if int(u["used"]) != used[u["email"]]: err(f"{u['email']}: used={u['used']} but approved annual days={used[u['email']]}")

# 6 generated formulas current
if subprocess.run([sys.executable, os.path.join(ROOT, "scripts/build_formula_docs.py"), "--check"], capture_output=True).returncode != 0:
    err("docs/power-fx-formulas.md is out of date: run scripts/build_formula_docs.py")

# 7 references and links; 8 forbidden headings
forbidden = re.compile(r"^#+\s.*(remaining work|incomplete features|future work)", re.I | re.M)
for f in files("**/*.md"):
    txt = open(f, encoding="utf-8").read(); base = os.path.dirname(f); nocode = re.sub(r"```.*?```", "", txt, flags=re.S)
    if forbidden.search(txt): err(f"forbidden heading in {rel(f)}")
    for ref in set(re.findall(r"`([A-Za-z0-9_./-]+/[A-Za-z0-9_.-]+\.(?:md|py|csv|fx|yaml|yml))`", txt)):
        if not (os.path.exists(os.path.join(ROOT, ref)) or os.path.exists(os.path.join(base, ref))):
            if not ref.startswith("docs/screenshots/0"): err(f"{rel(f)} references missing file `{ref}`")
    for link in set(re.findall(r"\]\(([^)#\s]+)\)", nocode)):
        if link.startswith(("http", "mailto")): continue
        if not os.path.exists(os.path.normpath(os.path.join(base, link))): err(f"{rel(f)} has broken link ({link})")
    if re.search(r"!\[[^\]]*\]\((?!http)[^)]+\)", nocode): err(f"{rel(f)} embeds an image that is not in the repository")
for v in {m for f in files("docs/*.md") for m in re.findall(r"\b(1000000\d\d)\b", open(f, encoding="utf-8").read())}:
    if int(v) not in {100000000, 100000001, 100000002}: err(f"invalid choice value {v}")

for e in errors: print("ERROR", e)
print(f"{len(cols)} columns checked | {len(errors)} error(s)")
sys.exit(1 if errors else 0)
