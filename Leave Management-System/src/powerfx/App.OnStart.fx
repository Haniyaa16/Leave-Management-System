Set(varMe, LookUp(Users, 'Primary Email' = User().Email));
Set(varIsManager, !IsBlank(LookUp(Users, Manager.'Primary Email' = User().Email)));
Set(varBalance, LookUp('Leave Balances', Employee.'Primary Email' = User().Email && 'Balance Year' = Year(Today())))
