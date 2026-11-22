# Power Fx formulas

> This page is generated from the files in `src/powerfx/` by `scripts/build_formula_docs.py`; do not edit it by hand.

The formulas refer to Dataverse **display names** (for example `'Leave Status'`, `'Days Requested'`). If your tables use different display names, change them in the source files and regenerate this page.

| Dataverse object | Display name used in Power Fx |
|---|---|
| Tables | `'Leave Requests'`, `'Leave Balances'`, `Users` |
| Leave Requests columns | `Employee`, `Manager`, `'Leave Type'`, `'Start Date'`, `'End Date'`, `'Days Requested'`, `Reason`, `'Leave Status'`, `'Manager Comments'`, `'Decision On'`, `'Balance Deducted'` |
| Leave Balances columns | `Employee`, `'Balance Year'`, `'Annual Leave Balance'`, `'Sick Leave Balance'`, `'Other Leave Balance'`, `'Total Used'`, `'Remaining Balance'` |
| Choices | `'LMS Leave Type'` (Annual, Sick, Others), `'LMS Leave Status'` (Pending, Approved, Rejected) |

## 1. App start-up

Source: `src/powerfx/App.OnStart.fx` (property `App.OnStart`)

Runs once when the app opens. It identifies the signed-in user in the Dataverse `Users` table, determines whether that user manages anyone (which controls the *Manager approval* button) and loads this year's leave balance record.

```text
Set(varMe, LookUp(Users, 'Primary Email' = User().Email));
Set(varIsManager, !IsBlank(LookUp(Users, Manager.'Primary Email' = User().Email)));
Set(varBalance, LookUp('Leave Balances', Employee.'Primary Email' = User().Email && 'Balance Year' = Year(Today())))
```

## 2. Working-day calculation

Source: `src/powerfx/screens/LeaveRequests.fx.yaml` - control `lblDays`, property `Text`

Builds one date for every day between the start and end date, keeps only Monday to Friday (`Weekday(..., StartOfWeek.Monday) < 6`) and counts them. The result is stored in *Days Requested*.

```text
CountRows(Filter(ForAll(Sequence(Max(0, DateDiff(dpStart.SelectedDate, dpEnd.SelectedDate, TimeUnit.Days) + 1), 0), DateAdd(dpStart.SelectedDate, Value, TimeUnit.Days)), Weekday(Value, StartOfWeek.Monday) < 6))
```

## 3. Request validation message

Source: `src/powerfx/screens/LeaveRequests.fx.yaml` - control `lblErr`, property `Text`

A single nested `If` returns the first rule that is broken, or an empty string when the request is valid. The Submit button is disabled while the message is not empty.

```text
If(IsBlank(varMe.Manager), "No manager is assigned to your user account. Contact the administrator.", If(dpEnd.SelectedDate < dpStart.SelectedDate, "End date cannot be before the start date.", If(And(ddType.Selected.Value <> "Sick", dpStart.SelectedDate < Today()), "Start date cannot be in the past (only Sick leave may be back-dated).", If(Value(lblDays.Text) = 0, "The selected range contains no working days.", If(IsBlank(Trim(txtReason.Text)), "Reason is required.", If(IsBlank(varBalance), "No leave balance record exists for this year.", If(And(ddType.Selected.Value = "Annual", Value(lblDays.Text) > varBalance.'Annual Leave Balance'), "Insufficient annual leave balance: " & varBalance.'Annual Leave Balance' & " day(s) available.", "")))))))
```

## 4. Overlap detection

Source: `src/powerfx/screens/LeaveRequests.fx.yaml` - control `lblOverlapCount`, property `Text`

Counts the employee's own Pending or Approved requests whose date range intersects the new range (`start <= newEnd` and `end >= newStart`). A count above zero shows a warning and requires the confirmation check box.

```text
CountRows(Filter('Leave Requests', Employee.'Primary Email' = User().Email, 'Leave Status' = 'LMS Leave Status'.Pending || 'Leave Status' = 'LMS Leave Status'.Approved, 'Start Date' <= dpEnd.SelectedDate, 'End Date' >= dpStart.SelectedDate))
```

## 5. Submit button state

Source: `src/powerfx/screens/LeaveRequests.fx.yaml` - control `btnSubmit`, property `DisplayMode`

Disables Submit while validation fails, while a save is running (prevents double submission) or while an overlap has not been acknowledged.

```text
If(lblErr.Text <> "" || locBusy || (lblOverlap.Visible && !chkConfirm.Value), DisplayMode.Disabled, DisplayMode.Edit)
```

## 6. Submit a leave request

Source: `src/powerfx/screens/LeaveRequests.fx.yaml` - control `btnSubmit`, property `OnSelect`

Creates the Dataverse row with status Pending, the employee's manager and the calculated days. `Errors()` is checked so a failed save is reported instead of silently ignored.

```text
UpdateContext({locBusy: true});
Patch('Leave Requests', Defaults('Leave Requests'), {
    'Request Title': ddType.Selected.Value & " leave - " & Text(dpStart.SelectedDate, "dd mmm yyyy"),
    Employee: varMe,
    Manager: varMe.Manager,
    'Leave Type': ddType.Selected,
    'Start Date': dpStart.SelectedDate,
    'End Date': dpEnd.SelectedDate,
    'Days Requested': Value(lblDays.Text),
    Reason: txtReason.Text,
    'Leave Status': 'LMS Leave Status'.Pending,
    'Balance Deducted': false
});
If(IsEmpty(Errors('Leave Requests')),
    Notify("Leave request submitted and sent to your manager.", NotificationType.Success);
    Reset(txtReason); Reset(chkConfirm),
    Notify(First(Errors('Leave Requests')).Message, NotificationType.Error));
UpdateContext({locBusy: false})
```

## 7. My requests list

Source: `src/powerfx/screens/LeaveRequests.fx.yaml` - control `galMine`, property `Items`

Shows only the signed-in employee's requests, filtered by status and sorted with the newest start date first.

```text
Sort(Filter('Leave Requests', Employee.'Primary Email' = User().Email, ddFilter.Selected.Value = "All" || 'Leave Status'.Value = ddFilter.Selected.Value), 'Start Date', SortOrder.Descending)
```

## 8. Manager's request list

Source: `src/powerfx/screens/ManagerApproval.fx.yaml` - control `galRequests`, property `Items`

Shows requests where the signed-in user is the Manager, never the user's own requests, filtered by the selected status view.

```text
Sort(Filter('Leave Requests', Manager.'Primary Email' = User().Email, Employee.'Primary Email' <> User().Email, ddView.Selected.Value = "All" || 'Leave Status'.Value = ddView.Selected.Value), 'Start Date', SortOrder.Ascending)
```

## 9. Approve a request and update the balance

Source: `src/powerfx/screens/ManagerApproval.fx.yaml` - control `btnApprove`, property `OnSelect`

Re-checks the annual balance, sets the request to Approved with comment and time, and - for Annual leave only - reduces *Annual Leave Balance* and *Remaining Balance* and increases *Total Used*. If the balance update fails, the approval is reverted to Pending.

```text
With({bal: LookUp('Leave Balances', Employee.'Primary Email' = ThisItem.Employee.'Primary Email' && 'Balance Year' = Year(ThisItem.'Start Date')), isAnnual: ThisItem.'Leave Type'.Value = "Annual"},
    If(isAnnual && (IsBlank(bal) || bal.'Annual Leave Balance' < ThisItem.'Days Requested'),
        Notify("Cannot approve: the employee does not have enough annual leave balance.", NotificationType.Error),
        Patch('Leave Requests', ThisItem, {'Leave Status': 'LMS Leave Status'.Approved, 'Manager Comments': txtRowComment.Text, 'Decision On': Now(), 'Balance Deducted': isAnnual});
        If(!IsEmpty(Errors('Leave Requests')),
            Notify(First(Errors('Leave Requests')).Message, NotificationType.Error),
            If(isAnnual,
                Patch('Leave Balances', bal, {'Annual Leave Balance': bal.'Annual Leave Balance' - ThisItem.'Days Requested', 'Total Used': bal.'Total Used' + ThisItem.'Days Requested', 'Remaining Balance': bal.'Remaining Balance' - ThisItem.'Days Requested'});
                If(!IsEmpty(Errors('Leave Balances')),
                    Patch('Leave Requests', ThisItem, {'Leave Status': 'LMS Leave Status'.Pending, 'Balance Deducted': false});
                    Notify("The balance could not be updated, so the approval was undone: " & First(Errors('Leave Balances')).Message, NotificationType.Error),
                    Notify("Request approved and annual leave balance updated.", NotificationType.Success)),
                Notify("Request approved. Sick and Other leave do not change the annual balance.", NotificationType.Success)))))
```

## 10. Reject button state

Source: `src/powerfx/screens/ManagerApproval.fx.yaml` - control `btnReject`, property `DisplayMode`

Rejection is available only when the manager has typed a comment.

```text
If(IsBlank(Trim(txtRowComment.Text)), DisplayMode.Disabled, DisplayMode.Edit)
```

## 11. Reject a request

Source: `src/powerfx/screens/ManagerApproval.fx.yaml` - control `btnReject`, property `OnSelect`

Sets the status to Rejected and stores the comment and decision time. No balance is changed.

```text
Patch('Leave Requests', ThisItem, {'Leave Status': 'LMS Leave Status'.Rejected, 'Manager Comments': txtRowComment.Text, 'Decision On': Now(), 'Balance Deducted': false});
If(IsEmpty(Errors('Leave Requests')), Notify("Request rejected.", NotificationType.Information), Notify(First(Errors('Leave Requests')).Message, NotificationType.Error))
```

## 12. Dashboard counters

Source: `src/powerfx/screens/ManagerApproval.fx.yaml` - control `lblPendingCount`, property `Text`

Counts the manager's Pending requests; the Approved and Rejected counters use the same pattern with the other status values.

```text
"Pending: " & CountRows(Filter('Leave Requests', Manager.'Primary Email' = User().Email, 'Leave Status' = 'LMS Leave Status'.Pending))
```
