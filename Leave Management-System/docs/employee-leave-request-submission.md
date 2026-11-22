# Employee leave request submission

Screen: **LeaveRequests** (`src/powerfx/screens/LeaveRequests.fx.yaml`)

## 1. Purpose
Allows an employee to see the current leave balance, apply for Annual, Sick or Other leave, and follow the status of earlier requests.

## 2. Screen layout
| Area | Controls | Content |
|---|---|---|
| Header | `lblTitle`, `btnManager` | title; *Manager approval* button, visible only to users who manage someone (`varIsManager`) |
| Balance summary | `lblBalAnnual`, `lblBalSick`, `lblBalOther`, `lblUsed` | values from the employee's balance record for the current year |
| Request form | `ddType`, `dpStart`, `dpEnd`, `txtReason`, `lblDays` | leave type, dates, reason and the calculated number of working days |
| Messages | `lblErr`, `lblOverlap`, `chkConfirm` | validation message, overlap warning and confirmation |
| Action | `btnSubmit` | creates the request |
| My requests | `ddFilter`, `galMine` | status filter and list showing type, dates, days, status and manager comment |

## 3. Submission procedure
1. Select the **leave type**.
2. Pick the **start** and **end** date. *Working days requested* updates immediately.
3. Enter the **reason**.
4. Read any message under the form. *Submit request* is enabled only when no message is shown.
5. If an overlap warning appears, tick *I understand and still want to submit*.
6. Select **Submit request**. A confirmation notification is shown and the request appears in *My leave requests* with status **Pending**.

## 4. Validation rules
| # | Rule | Message shown |
|---|---|---|
| 1 | The employee has a manager in Dataverse | "No manager is assigned to your user account. Contact the administrator." |
| 2 | End date is not before start date | "End date cannot be before the start date." |
| 3 | Start date is not in the past (Sick leave may be back-dated) | "Start date cannot be in the past (only Sick leave may be back-dated)." |
| 4 | The range contains at least one working day | "The selected range contains no working days." |
| 5 | Reason is not blank | "Reason is required." |
| 6 | A balance record exists for the current year | "No leave balance record exists for this year." |
| 7 | Annual leave: days requested do not exceed the annual balance | "Insufficient annual leave balance: N day(s) available." |

Rules are evaluated in this order and only the first violated rule is displayed.

## 5. Working days
Days Requested counts Monday to Friday between the start and end date, inclusive. Public holidays are not excluded.

## 6. Overlap warning
The app counts the employee's own **Pending** and **Approved** requests whose period intersects the new period. A non-zero count shows an amber warning and keeps *Submit request* disabled until the confirmation box is ticked. The warning does not block the request because an employee may intentionally replace or extend earlier leave.

## 7. Data written on submission
| Column | Value |
|---|---|
| Request Title | `<Leave Type> leave - <dd mmm yyyy of start date>` |
| Employee | signed-in user |
| Manager | the signed-in user's Manager |
| Leave Type / Start Date / End Date / Reason | as entered |
| Days Requested | calculated working days |
| Leave Status | Pending |
| Balance Deducted | No |

The formulas are listed in [power-fx-formulas.md](power-fx-formulas.md) (sections 2-7).
