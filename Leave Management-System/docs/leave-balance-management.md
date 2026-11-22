# Leave balance management

## 1. Balance record
Every employee has one **Leave Balances** row per calendar year. The administrator creates the rows at the start of the year in the Dataverse table (or imports them from a CSV file such as `sample-data/sample_users.csv`). The app reads the row where *Balance Year* equals the current year.

## 2. Leave rules
| Leave type | Effect of an approved request |
|---|---|
| **Annual** | reduces *Annual Leave Balance* and *Remaining Balance*, increases *Total Used* by *Days Requested* |
| **Sick** | no change to any balance |
| **Others** | no change to any balance |

*Sick Leave Balance* and *Other Leave Balance* hold the entitlements shown to the employee; the application does not reduce them.

## 3. When the balance changes
| Event | Balance effect |
|---|---|
| Employee submits a request | none (the request is Pending) |
| Manager approves Annual leave | deduction |
| Manager approves Sick / Others leave | none |
| Manager rejects any request | none |

## 4. Formulas
For an approved Annual request with *d* = *Days Requested* and the employee's balance row *b*:
```
b.Annual Leave Balance  = b.Annual Leave Balance  - d
b.Total Used            = b.Total Used            + d
b.Remaining Balance     = b.Remaining Balance     - d
```
Pre-conditions checked in the app: at submission `d <= Annual Leave Balance`; at approval the same check is repeated against the current balance row, so two pending requests cannot together overdraw the balance.

## 5. Worked example (illustrative arithmetic using `sample-data/sample_users.csv`)
Fatima Rahman starts 2026 with 23 annual days, 9 sick days and 5 other days (*Remaining Balance* = 37). Her approved 5-day Annual request on 10-14 Aug 2026 gives:
| Column | Before | After |
|---|---|---|
| Annual Leave Balance | 23 | 18 |
| Total Used | 0 | 5 |
| Remaining Balance | 37 | 32 |
| Sick Leave Balance | 9 | 9 |
| Other Leave Balance | 5 | 5 |

## 6. Consistency safeguards
- **Balance Deducted** is stored on every request: Yes only when that approval reduced the annual balance.
- The request update and the balance update are performed together; if the balance update fails the request is reverted to Pending.
- Auditing is enabled on both tables, so every change to a balance is traceable.
- Rows can be reconciled at any time: *Total Used* for a year equals the sum of *Days Requested* of that employee's Approved Annual requests.

The formula that implements these rules is section 9 of [power-fx-formulas.md](power-fx-formulas.md).
