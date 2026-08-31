import React, {createContext, useContext, useMemo, useState} from 'react';

const AppContext = createContext(null);

const defaultCondition = 'stiffness';

export function AppProvider({children}){
  const [params,setParams]=useState({
    conditions:[defaultCondition],
    condition:defaultCondition,
    preference:'high',
    intercepts:{},
    intercept:null,
    syncLines:true,
  });
  // Axis boundaries (X/Y min/max), keyed per chart (by condition) -- each chart
  // has its own independent bounds instead of one set shared by every diagram.
  // Unlike hiddenGroups, these DO need to reach the backend (they change which
  // materials analyze() considers), so useDiagramData's bodyFor merges the
  // current chart's entry into its request instead of reading a global field.
  const [axisBoundsByCondition,setAxisBoundsByCondition]=useState({});
  const setAxisBoundsFor = (condition, patch) => setAxisBoundsByCondition(prev => ({
    ...prev,
    [condition]: {...(prev[condition] || {}), ...patch},
  }));
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
  const value=useMemo(()=>({params,setParams,hiddenGroupsByCondition,setHiddenGroupsFor,toggleGroup,axisBoundsByCondition,setAxisBoundsFor}),[params,hiddenGroupsByCondition,axisBoundsByCondition]);
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export const useApp = () => useContext(AppContext);
