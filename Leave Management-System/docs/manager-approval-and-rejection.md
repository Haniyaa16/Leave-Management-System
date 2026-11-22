# Manager approval and rejection

Screen: **ManagerApproval** (`src/powerfx/screens/ManagerApproval.fx.yaml`)

## 1. Who is a manager
A user is a manager when at least one Dataverse user has that person in the **Manager** field. The *Manager approval* button on the `LeaveRequests` screen is shown only to such users. Each request stores its approver in the **Manager** column, copied from the employee at submission.

## 2. Screen layout
| Area | Controls | Content |
|---|---|---|
| Header | `btnBack`, `lblTitle` | back to *My requests*; screen title |
| Dashboard counters | `lblPendingCount`, `lblApprovedCount`, `lblRejectedCount` | number of the manager's requests in each status |
| View selector | `ddView` | Pending (default), Approved, Rejected or All |
| Request list | `galRequests` | employee, type, days, dates, status, reason, comment box, *Approve* and *Reject* buttons |

The list never contains the manager's own requests.

## 3. Approving a request
1. The manager optionally types a comment and selects **Approve**.
2. For Annual leave the app reads the employee's balance row for the year of the start date and checks that *Annual Leave Balance* is at least *Days Requested*; otherwise approval is refused with a message.
3. The request is updated: *Leave Status* = Approved, *Manager Comments*, *Decision On* = now, *Balance Deducted* = Yes for Annual leave (No for Sick and Others).
4. For Annual leave the balance row is updated (see [leave-balance-management.md](leave-balance-management.md)).
5. If the balance update fails, the request is returned to **Pending** and an error message explains why, so a request is never approved without its balance effect.
6. Buttons and the comment box disappear/lock because the request is no longer Pending.

## 4. Rejecting a request
1. The manager must type a comment; until then **Reject** is disabled.
2. The request is updated: *Leave Status* = Rejected, *Manager Comments*, *Decision On* = now, *Balance Deducted* = No.
3. No balance is changed.

## 5. What the employee sees
In *My leave requests* the status is coloured (green Approved, red Rejected, amber Pending) and the manager's comment is shown under the request.

## 6. Authorisation
The list is filtered to requests where the signed-in user is the Manager, and decisions can only be taken on Pending requests. Server-side permissions are provided by the Dataverse security roles in [security-and-roles.md](security-and-roles.md).

The formulas are listed in [power-fx-formulas.md](power-fx-formulas.md) (sections 8-12).
