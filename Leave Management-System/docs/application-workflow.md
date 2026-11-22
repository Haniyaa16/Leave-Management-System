# Application workflow

## 1. Request life cycle
```mermaid
stateDiagram-v2
    [*] --> Pending: Employee submits request
    Pending --> Approved: Manager approves
    Pending --> Rejected: Manager rejects (comment required)
    Approved --> [*]
    Rejected --> [*]
```

## 2. End-to-end sequence
```mermaid
sequenceDiagram
    actor E as Employee
    participant LR as LeaveRequests screen
    participant DV as Dataverse
    participant MA as ManagerApproval screen
    actor M as Manager
    E->>LR: Open app
    LR->>DV: Read user, manager status, balance
    E->>LR: Enter type, dates, reason
    LR->>LR: Validate (dates, working days, overlap, balance)
    LR->>DV: Create Leave Request (Pending)
    M->>MA: Open Manager approval
    MA->>DV: Read requests where Manager = me
    alt Approve
        MA->>DV: Check balance (Annual only)
        MA->>DV: Update request to Approved
        MA->>DV: Update Leave Balance (Annual only)
    else Reject
        MA->>DV: Update request to Rejected with comment
    end
    E->>LR: View status and manager comment
```

## 3. Responsibilities
| Step | Actor | Screen | Data change |
|---|---|---|---|
| 1 | Employee | LeaveRequests | Leave Requests row created: Pending, Balance Deducted = No |
| 2 | Manager | ManagerApproval | request set to Approved or Rejected with comment and time |
| 3 | System (Power Fx) | ManagerApproval | Annual approvals only: Leave Balances row updated, Balance Deducted = Yes |
| 4 | Employee | LeaveRequests | reads status and comment (no change) |

## 4. Rules summary
- One manager per employee, taken from the Dataverse **Manager** field.
- A manager never approves his or her own request (own requests are excluded from the list).
- Only Pending requests can be decided; decisions are final in the application.
- Rejection needs a comment; approval comment is optional.
- Only approved Annual leave changes a balance.
