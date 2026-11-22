# Installation and setup guide

This guide builds the complete system in a Power Platform environment. If the tables and the app already exist in your environment, use the sections as a checklist and make sure the display names match those listed in [power-fx-formulas.md](power-fx-formulas.md).

## 1. Prerequisites
| Item | Requirement |
|---|---|
| Account | Microsoft Entra ID work or school account with Power Apps access |
| Environment | Power Platform environment with a **Dataverse** database (a Developer environment is sufficient for study) |
| Licences | Power Apps licence that allows Dataverse custom tables for the app users (verify in Microsoft's current licensing guide) |
| Roles | System Administrator (or System Customizer) to create tables and roles |
| Tools | Python 3.9 or later for the schema and sample-data scripts |

## 2. Get the project
```bash
git clone <your-repository-url>
cd Leave-Request-and-Approval-Management-System
pip install -r dataverse/requirements.txt
```

## 3. Create the publisher and solution
1. Open <https://make.powerapps.com> and select your environment.
2. **Solutions > New solution**: display name *Leave Management*, name `LeaveManagement`.
3. **New publisher**: prefix `lrs` (any prefix works; then set `PUBLISHER_PREFIX` to it in the next step).

## 4. Create the Dataverse tables
```bash
cd dataverse
export DATAVERSE_URL=https://yourorg.crm.dynamics.com
export SOLUTION_UNIQUE_NAME=LeaveManagement
export PUBLISHER_PREFIX=lrs
python create_schema.py
```
On Windows PowerShell use `$env:DATAVERSE_URL = "..."`. Sign in at the device-code page shown in the terminal. The script creates the two choices, the tables **Leave Requests** and **Leave Balances**, all columns and lookups, publishes them and prints a verification line per table. It can be run again safely.
If your tenant blocks the default sign-in client, register an Entra ID public-client app and set `LRS_CLIENT_ID` and `LRS_TENANT_ID` (see `dataverse/_common.py`).

## 5. Security roles and users
1. Create the roles described in [security-and-roles.md](security-and-roles.md) and assign them.
2. For every employee set the **Manager** field (Power Platform admin center > Users).
3. Create one **Leave Balances** row per employee for the current year (table editor, import, or the sample loader below).

## 6. Create the canvas app
1. In the solution choose **New > App > Canvas app** (Tablet format) and name it *Leave Request & Approval Management System*.
2. **Data > Add data**: add **Leave Requests**, **Leave Balances** and **Users**.
3. Create two screens named exactly `LeaveRequests` and `ManagerApproval`.
4. Paste `src/powerfx/App.OnStart.fx` into **App > OnStart** and choose *Run OnStart*.
5. Copy the text of each file in `src/powerfx/screens/` and paste it into the screen with the same name (or create the controls listed in the file by name and set each property to its formula). Use classic controls (`label`, `button`, `text`, `dropdown`, `datepicker`, `checkbox`, `gallery`).
6. Save and **Publish**.

## 7. Sample data (optional)
1. Replace `YOURTENANT.onmicrosoft.com` in `sample-data/sample_users.csv` and `sample_requests.csv` with real, enabled users of your environment.
2. Run:
```bash
cd dataverse
python seed_sample_data.py           # add --reset to remove earlier SAMPLE rows first
```
The loader sets the managers, creates the balances and requests, and is safe to run again.

## 8. Share and use
Share the app with the employees' group, copy the app link and open it. Employees use the `LeaveRequests` screen; managers use the *Manager approval* button.

## 9. Repository checks
```bash
python scripts/validate_repository.py
```
The check runs offline (no environment needed) and also runs in GitHub Actions on every push.
