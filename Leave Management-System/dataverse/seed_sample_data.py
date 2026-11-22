#!/usr/bin/env python3
"""
Loads the illustrative sample data in ../sample-data into Dataverse: sets each sample user's Manager, creates the
Leave Balances and Leave Requests rows. Titles start with 'SAMPLE ' so they can be removed with --reset.
Before running: replace YOURTENANT.onmicrosoft.com in both CSV files with real, enabled users of your environment.
Usage: DATAVERSE_URL=https://yourorg.crm.dynamics.com PUBLISHER_PREFIX=lrs python seed_sample_data.py [--reset]
Needs the System Administrator role (it sets users' Manager and record owners). Idempotent.
"""
import os, sys, csv
from _common import get_org, session

ORG = get_org()
P = os.environ.get("PUBLISHER_PREFIX", "lrs").lower()
API = f"{ORG}/api/data/v9.2"
S = session(ORG)
DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sample-data")
TYPE = {"Annual": 100000000, "Sick": 100000001, "Others": 100000002}
STATUS = {"Pending": 100000000, "Approved": 100000001, "Rejected": 100000002}
_ids = {}


def rows(name):
    with open(os.path.join(DIR, name), newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def uid(email):
    if email not in _ids:
        r = S.get(f"{API}/systemusers", params={"$select": "systemuserid", "$filter": f"internalemailaddress eq '{email}' and isdisabled eq false"})
        v = r.json().get("value", [])
        if not v:
            sys.exit(f"User not found or disabled in Dataverse: {email} (edit sample-data/*.csv)")
        _ids[email] = v[0]["systemuserid"]
    return _ids[email]


def bind(email):
    return f"/systemusers({uid(email)})"


def exists(entityset, flt):
    return bool(S.get(f"{API}/{entityset}", params={"$top": 1, "$filter": flt}).json().get("value"))


def check(r, what):
    if r.status_code >= 300:
        sys.exit(f"FAILED {what}: {r.status_code} {r.text[:500]}")


users, reqs = rows("sample_users.csv"), rows("sample_requests.csv")
byemail = {u["email"]: u for u in users}

if "--reset" in sys.argv:
    for es, pk, namecol in ((f"{P}_leaverequests", f"{P}_leaverequestid", f"{P}_requesttitle"),
                            (f"{P}_leavebalances", f"{P}_leavebalanceid", f"{P}_balancetitle")):
        for rec in S.get(f"{API}/{es}", params={"$select": pk, "$filter": f"startswith({namecol},'SAMPLE ')"}).json().get("value", []):
            S.delete(f"{API}/{es}({rec[pk]})")
    print("previous sample rows deleted")

print("Managers and balances")
for u in users:
    if u["manager_email"]:
        check(S.patch(f"{API}/systemusers({uid(u['email'])})", json={"parentsystemuserid@odata.bind": bind(u["manager_email"])}), "manager " + u["email"])
    if exists(f"{P}_leavebalances", f"_{P}_employee_value eq {uid(u['email'])} and {P}_balanceyear eq {u['year']}"):
        print("  balance exists", u["email"]); continue
    check(S.post(f"{API}/{P}_leavebalances", json={
        f"{P}_BalanceTitle": f"SAMPLE {u['name']} - {u['year']}", f"{P}_Employee@odata.bind": bind(u["email"]),
        "ownerid@odata.bind": bind(u["email"]), f"{P}_BalanceYear": int(u["year"]),
        f"{P}_AnnualLeaveBalance": int(u["annual"]), f"{P}_SickLeaveBalance": int(u["sick"]), f"{P}_OtherLeaveBalance": int(u["other"]),
        f"{P}_TotalUsed": int(u["used"]), f"{P}_RemainingBalance": int(u["annual"]) + int(u["sick"]) + int(u["other"])}), "balance " + u["email"])
    print("  balance created", u["email"])

print("Requests")
for q in reqs:
    emp = byemail[q["employee_email"]]
    title = f"SAMPLE {q['type']} leave - {q['start']} - {emp['name']}"
    if exists(f"{P}_leaverequests", f"{P}_requesttitle eq '{title}'"):
        print("  request exists", title); continue
    decided = q["status"] != "Pending"
    body = {f"{P}_RequestTitle": title, f"{P}_Employee@odata.bind": bind(emp["email"]), "ownerid@odata.bind": bind(emp["email"]),
            f"{P}_LeaveType": TYPE[q["type"]], f"{P}_StartDate": q["start"], f"{P}_EndDate": q["end"], f"{P}_Reason": q["reason"],
            f"{P}_DaysRequested": int(q["days"]), f"{P}_LeaveStatus": STATUS[q["status"]],
            f"{P}_BalanceDeducted": q["status"] == "Approved" and q["type"] == "Annual"}
    if emp["manager_email"]:
        body[f"{P}_Manager@odata.bind"] = bind(emp["manager_email"])
    if decided:
        body[f"{P}_ManagerComments"] = q["comments"]
        body[f"{P}_DecisionOn"] = f"{q['decided_on']}T09:00:00Z"
    check(S.post(f"{API}/{P}_leaverequests", json=body), title)
    print("  request created", title)
print("Done.")
