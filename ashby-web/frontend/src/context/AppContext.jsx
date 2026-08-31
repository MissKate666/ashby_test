import React, {createContext, useContext, useMemo, useState} from 'react';

const AppContext = createContext(null);

const defaultCondition = 'stiffness';

export function AppProvider({children}){
  const [params,setParams]=useState({
    conditions:[defaultCondition],
    condition:defaultCondition,
    preference:'high',
    x_min:'',
    x_max:'',
    y_min:'',
    y_max:'',
    intercepts:{},
    intercept:null,
    syncLines:true,
  });
  // Legend group visibility, keyed per chart (by condition). Kept out of `params`
  // on purpose: params drives the analyze() request to the backend (see
  // useDiagramData's bodyFor), and hiding a group is a pure client-side display
  // filter -- it must not trigger a refetch, move the criterion line, or change
  // what the backend counts as suitable. Each chart gets its own entry so hiding a
  // group on one diagram never affects another: a chart with no entry yet (new,
  // or never touched) simply has nothing hidden, independent of every other chart.
  const [hiddenGroupsByCondition,setHiddenGroupsByCondition]=useState({});
  const setHiddenGroupsFor = (condition, set) => setHiddenGroupsByCondition(prev => ({...prev, [condition]: set}));
  const toggleGroup = (condition, name) => setHiddenGroupsByCondition(prev => {
    const next = new Set(prev[condition] ?? []);
    if (next.has(name)) next.delete(name); else next.add(name);
    return {...prev, [condition]: next};
  });
  const value=useMemo(()=>({params,setParams,hiddenGroupsByCondition,setHiddenGroupsFor,toggleGroup}),[params,hiddenGroupsByCondition]);
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export const useApp = () => useContext(AppContext);
