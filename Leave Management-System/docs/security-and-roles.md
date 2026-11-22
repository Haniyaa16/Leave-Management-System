# Security and roles

## 1. Authentication
Users sign in with Microsoft Entra ID. The app identifies the user through `User().Email` and matches it with *Primary Email* in the Dataverse **Users** table.

## 2. Dataverse security roles
Create the roles by **copying the *Basic User* role** (it keeps the privileges needed to run Power Apps and read users) and then set the privileges below on the custom tables.

| Role | Leave Requests | Leave Balances | Assigned to |
|---|---|---|---|
| **LMS Employee** | Create, Read, Append, Append To - *User* | Read - *User* | every employee |
| **LMS Manager** | Read, Write, Append, Append To - *Business Unit* | Read, Write - *Business Unit* | managers (in addition to LMS Employee) |
| **LMS Administrator** | Create, Read, Write - *Organization* | Create, Read, Write - *Organization* | the person who maintains balances |

Privilege scopes: *User* = rows the user owns; *Business Unit* = rows owned by anyone in the user's business unit; *Organization* = all rows.

## 3. Design notes
- The *Manager* role needs **Write** on Leave Balances because the approval formula updates the employee's balance row from the app.
- *Business Unit* scope exposes all requests of the unit to its managers. Where reporting lines must be enforced by the platform, Dataverse **manager hierarchy security** can be enabled; check the Microsoft documentation for the privileges it grants before relying on it for updates.
- Each request and balance is owned by the employee (user-owned tables), so employees see only their own rows.
- Auditing is enabled on both tables by the schema script; auditing must also be switched on for the environment (Power Platform admin center > Settings > Audit settings).

## 4. Sharing the app
Share the canvas app with the employees' group (permission *Can use*). Sharing the app does not grant data access; the security roles above are also required.
