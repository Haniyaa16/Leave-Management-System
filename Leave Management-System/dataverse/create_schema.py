#!/usr/bin/env python3
"""
Creates the Dataverse data model of the Leave Request & Approval Management System
(tables LeaveRequests and LeaveBalances, two choices, lookups to Users) through the Dataverse Web API
and adds each component to an UNMANAGED solution you own.

Prerequisites
  pip install -r requirements.txt
  An unmanaged solution and its publisher already exist (docs/setup-guide.md, step 3).
Usage
  DATAVERSE_URL=https://yourorg.crm.dynamics.com SOLUTION_UNIQUE_NAME=LeaveManagement PUBLISHER_PREFIX=lrs python create_schema.py
Environment variables
  DATAVERSE_URL (required) | SOLUTION_UNIQUE_NAME (default LeaveManagement) | PUBLISHER_PREFIX (default lrs; must equal the
  solution publisher's prefix) | LANGUAGE_CODE (default 1033) | LRS_CLIENT_ID / LRS_TENANT_ID (see _common.py)
Re-runnable: every object is looked up first and skipped when it exists.
"""
import os, sys
from _common import get_org, session

ORG = get_org()
SOLUTION = os.environ.get("SOLUTION_UNIQUE_NAME", "LeaveManagement")
P = os.environ.get("PUBLISHER_PREFIX", "lrs").lower()
LANG = int(os.environ.get("LANGUAGE_CODE", "1033"))
API = f"{ORG}/api/data/v9.2"
S = session(ORG, SOLUTION)


def L(t):
    return {"@odata.type": "Microsoft.Dynamics.CRM.Label", "LocalizedLabels": [
        {"@odata.type": "Microsoft.Dynamics.CRM.LocalizedLabel", "Label": t, "LanguageCode": LANG}]}


def REQ(level="None"):
    return {"Value": level, "CanBeChanged": True, "ManagedPropertyLogicalName": "canmodifyrequirementlevelsettings"}


def exists(path):
    r = S.get(f"{API}/{path}")
    if r.status_code == 404:
        return False
    if r.status_code >= 400:
        sys.exit(f"Lookup failed for {path}: {r.status_code} {r.text[:400]}")
    return True


def post(path, body, what):
    r = S.post(f"{API}/{path}", json=body)
    if r.status_code < 300:
        print(f"  created  {what}")
    else:
        sys.exit(f"  FAILED   {what}: {r.status_code}\n{r.text[:900]}")


# ---- pre-checks -------------------------------------------------------------------------------
sol = S.get(f"{API}/solutions?$select=uniquename,ismanaged&$expand=publisherid($select=customizationprefix)"
            f"&$filter=uniquename eq '{SOLUTION}'").json().get("value", [])
if not sol:
    sys.exit(f"Solution '{SOLUTION}' not found. Create it first (docs/setup-guide.md, step 3).")
if sol[0]["publisherid"]["customizationprefix"].lower() != P:
    sys.exit(f"Publisher prefix is '{sol[0]['publisherid']['customizationprefix']}' but PUBLISHER_PREFIX is '{P}'.")
if sol[0].get("ismanaged"):
    sys.exit("The solution is managed; use an unmanaged solution.")

# ---- 1. choices -------------------------------------------------------------------------------
OPTIONSETS = {
    f"{P}_leavetype":   ("LMS Leave Type",   ["Annual", "Sick", "Others"]),
    f"{P}_leavestatus": ("LMS Leave Status", ["Pending", "Approved", "Rejected"]),
}
print("Choices (values start at 100000000, in listed order)")
for name, (disp, labels) in OPTIONSETS.items():
    if exists(f"GlobalOptionSetDefinitions(Name='{name}')?$select=Name"):
        print(f"  exists   {disp}")
        continue
    post("GlobalOptionSetDefinitions", {
        "@odata.type": "Microsoft.Dynamics.CRM.OptionSetMetadata", "Name": name, "DisplayName": L(disp),
        "OptionSetType": "Picklist", "IsGlobal": True,
        "Options": [{"Value": 100000000 + i, "Label": L(t)} for i, t in enumerate(labels)]}, disp)

_os = {}


def os_id(name):
    if name not in _os:
        _os[name] = S.get(f"{API}/GlobalOptionSetDefinitions(Name='{name}')?$select=MetadataId").json()["MetadataId"]
    return _os[name]


# ---- 2. column helpers ------------------------------------------------------------------------
def col(entity, schema, body, what):
    if exists(f"EntityDefinitions(LogicalName='{entity}')/Attributes(LogicalName='{schema.lower()}')?$select=LogicalName"):
        print(f"  exists   {entity}.{schema.lower()}")
        return
    post(f"EntityDefinitions(LogicalName='{entity}')/Attributes", body, what)


def base(odata, atype, tname, schema, disp, req):
    return {"@odata.type": f"Microsoft.Dynamics.CRM.{odata}", "AttributeType": atype,
            "AttributeTypeName": {"Value": tname}, "SchemaName": schema, "DisplayName": L(disp), "RequiredLevel": REQ(req)}


def c_pick(e, schema, disp, osname, req="None", default=None):
    b = base("PicklistAttributeMetadata", "Picklist", "PicklistType", schema, disp, req)
    b["GlobalOptionSet@odata.bind"] = f"/GlobalOptionSetDefinitions({os_id(osname)})"
    if default is not None:
        b["DefaultFormValue"] = default
    col(e, schema, b, f"{e}.{schema}")


def c_date(e, schema, disp, req="None"):
    b = base("DateTimeAttributeMetadata", "DateTime", "DateTimeType", schema, disp, req)
    b.update({"Format": "DateOnly", "DateTimeBehavior": {"Value": "DateOnly"}})
    col(e, schema, b, f"{e}.{schema}")


def c_datetime(e, schema, disp, req="None"):
    b = base("DateTimeAttributeMetadata", "DateTime", "DateTimeType", schema, disp, req)
    b.update({"Format": "DateAndTime", "DateTimeBehavior": {"Value": "UserLocal"}})
    col(e, schema, b, f"{e}.{schema}")


def c_int(e, schema, disp, req="None", lo=-1000, hi=100000):
    b = base("IntegerAttributeMetadata", "Integer", "IntegerType", schema, disp, req)
    b.update({"Format": "None", "MinValue": lo, "MaxValue": hi})
    col(e, schema, b, f"{e}.{schema}")


def c_memo(e, schema, disp, req="None"):
    b = base("MemoAttributeMetadata", "Memo", "MemoType", schema, disp, req)
    b.update({"Format": "TextArea", "MaxLength": 2000})
    col(e, schema, b, f"{e}.{schema}")


def c_str(e, schema, disp, req="None", n=200):
    b = base("StringAttributeMetadata", "String", "StringType", schema, disp, req)
    b.update({"MaxLength": n, "FormatName": {"Value": "Text"}})
    col(e, schema, b, f"{e}.{schema}")


def c_bool(e, schema, disp, default=False):
    b = base("BooleanAttributeMetadata", "Boolean", "BooleanType", schema, disp, "None")
    b.update({"DefaultValue": default, "OptionSet": {
        "@odata.type": "Microsoft.Dynamics.CRM.BooleanOptionSetMetadata", "OptionSetType": "Boolean",
        "TrueOption": {"Value": 1, "Label": L("Yes")}, "FalseOption": {"Value": 0, "Label": L("No")}}})
    col(e, schema, b, f"{e}.{schema}")


def c_lookup(referencing, schema, disp, rel, req="None"):
    if exists(f"EntityDefinitions(LogicalName='{referencing}')/Attributes(LogicalName='{schema.lower()}')?$select=LogicalName"):
        print(f"  exists   {referencing}.{schema.lower()}")
        return
    post("RelationshipDefinitions", {
        "@odata.type": "Microsoft.Dynamics.CRM.OneToManyRelationshipMetadata", "SchemaName": rel,
        "ReferencedEntity": "systemuser", "ReferencingEntity": referencing,
        "Lookup": {"@odata.type": "Microsoft.Dynamics.CRM.LookupAttributeMetadata", "AttributeType": "Lookup",
                   "AttributeTypeName": {"Value": "LookupType"}, "SchemaName": schema, "DisplayName": L(disp),
                   "RequiredLevel": REQ(req)},
        "AssociatedMenuConfiguration": {"Behavior": "UseCollectionName", "Group": "Details", "Label": L(disp), "Order": 10000},
        "CascadeConfiguration": {"Assign": "NoCascade", "Delete": "Restrict", "Merge": "NoCascade",
                                 "Reparent": "NoCascade", "Share": "NoCascade", "Unshare": "NoCascade"}},
         f"{referencing}.{schema} -> systemuser")


def table(schema, disp, plural, primary_schema, primary_disp):
    logical = schema.lower()
    if exists(f"EntityDefinitions(LogicalName='{logical}')?$select=LogicalName"):
        print(f"  exists   table {logical}")
        return
    post("EntityDefinitions", {
        "@odata.type": "Microsoft.Dynamics.CRM.EntityMetadata", "SchemaName": schema, "DisplayName": L(disp),
        "DisplayCollectionName": L(plural), "Description": L(f"{disp} - Leave Request & Approval Management System"),
        "OwnershipType": "UserOwned", "HasNotes": False, "HasActivities": False, "IsActivity": False,
        "IsAuditEnabled": {"Value": True, "CanBeChanged": True, "ManagedPropertyLogicalName": "canmodifyauditsettings"},
        "Attributes": [{"@odata.type": "Microsoft.Dynamics.CRM.StringAttributeMetadata", "AttributeType": "String",
                        "AttributeTypeName": {"Value": "StringType"}, "SchemaName": primary_schema, "IsPrimaryName": True,
                        "RequiredLevel": REQ("ApplicationRequired"), "MaxLength": 200,
                        "FormatName": {"Value": "Text"}, "DisplayName": L(primary_disp)}]}, f"table {logical}")


# ---- 3. LeaveRequests -------------------------------------------------------------------------
LR = f"{P}_leaverequest"
print("Table: Leave Requests")
table(f"{P}_LeaveRequest", "Leave Request", "Leave Requests", f"{P}_RequestTitle", "Request Title")
c_lookup(LR, f"{P}_Employee", "Employee", f"{P}_systemuser_leaverequest_employee", "ApplicationRequired")
c_lookup(LR, f"{P}_Manager", "Manager", f"{P}_systemuser_leaverequest_manager")
c_pick(LR, f"{P}_LeaveType", "Leave Type", f"{P}_leavetype", "ApplicationRequired")
c_date(LR, f"{P}_StartDate", "Start Date", "ApplicationRequired")
c_date(LR, f"{P}_EndDate", "End Date", "ApplicationRequired")
c_int(LR, f"{P}_DaysRequested", "Days Requested", "ApplicationRequired", 0, 365)
c_memo(LR, f"{P}_Reason", "Reason", "ApplicationRequired")
c_pick(LR, f"{P}_LeaveStatus", "Leave Status", f"{P}_leavestatus", "ApplicationRequired", default=100000000)
c_str(LR, f"{P}_ManagerComments", "Manager Comments", "None", 500)
c_datetime(LR, f"{P}_DecisionOn", "Decision On")
c_bool(LR, f"{P}_BalanceDeducted", "Balance Deducted", False)

# ---- 4. LeaveBalances -------------------------------------------------------------------------
LB = f"{P}_leavebalance"
print("Table: Leave Balances")
table(f"{P}_LeaveBalance", "Leave Balance", "Leave Balances", f"{P}_BalanceTitle", "Balance Title")
c_lookup(LB, f"{P}_Employee", "Employee", f"{P}_systemuser_leavebalance_employee", "ApplicationRequired")
c_int(LB, f"{P}_BalanceYear", "Balance Year", "ApplicationRequired", 2000, 2100)
c_int(LB, f"{P}_AnnualLeaveBalance", "Annual Leave Balance", "ApplicationRequired")
c_int(LB, f"{P}_SickLeaveBalance", "Sick Leave Balance", "ApplicationRequired")
c_int(LB, f"{P}_OtherLeaveBalance", "Other Leave Balance", "ApplicationRequired")
c_int(LB, f"{P}_TotalUsed", "Total Used", "ApplicationRequired")
c_int(LB, f"{P}_RemainingBalance", "Remaining Balance", "ApplicationRequired")

# ---- 5. publish and verify --------------------------------------------------------------------
r = S.post(f"{API}/PublishAllXml", json={})
print("Published." if r.status_code < 300 else f"Publish failed: {r.status_code} {r.text[:300]}")
for ent, minimum in {LR: 12, LB: 8}.items():
    n = len(S.get(f"{API}/EntityDefinitions(LogicalName='{ent}')/Attributes?$filter=startswith(LogicalName,'{P}_')&$select=LogicalName").json()["value"])
    print(f"verify   {ent}: {n} custom columns (expected >= {minimum})", "OK" if n >= minimum else "<-- CHECK")
