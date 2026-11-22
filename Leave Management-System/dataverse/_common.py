"""Shared helpers for the Dataverse scripts (auth + HTTP session)."""
import os, sys, requests, msal

# Microsoft's public sample client id. Some tenants block it - then register your own app
# (Entra ID > App registrations > Public client, redirect http://localhost, API permission
# Dynamics CRM > user_impersonation) and set LRS_CLIENT_ID (+ LRS_TENANT_ID).
DEFAULT_CLIENT_ID = "51f81489-12ee-4a9e-aaae-a2591f45987d"


def get_org():
    org = os.environ.get("DATAVERSE_URL", "").rstrip("/")
    if not org:
        sys.exit("Set DATAVERSE_URL, e.g. https://yourorg.crm.dynamics.com (no trailing path).")
    return org


def session(org, solution=None):
    client_id = os.environ.get("LRS_CLIENT_ID", DEFAULT_CLIENT_ID)
    tenant = os.environ.get("LRS_TENANT_ID", "organizations")
    app = msal.PublicClientApplication(client_id, authority=f"https://login.microsoftonline.com/{tenant}")
    flow = app.initiate_device_flow(scopes=[f"{org}/.default"])
    if "message" not in flow:
        sys.exit(f"Could not start sign-in: {flow}")
    print(flow["message"])
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        sys.exit(f"Sign-in failed: {result.get('error_description', result)}")
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {result['access_token']}",
                      "Content-Type": "application/json; charset=utf-8", "Accept": "application/json",
                      "OData-MaxVersion": "4.0", "OData-Version": "4.0"})
    if solution:
        s.headers["MSCRM.SolutionUniqueName"] = solution
    return s
