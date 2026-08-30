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
  // Legend group visibility. Kept out of `params` on purpose: params drives the
  // analyze() request to the backend (see useDiagramData's bodyFor), and hiding a
  // group is a pure client-side display filter -- it must not trigger a refetch,
  // move the criterion line, or change what the backend counts as suitable. It's
  // also intentionally *not* reset when params change (criterion/filters/etc.):
  // the same set of material groups exists across every criterion, so carrying the
  // user's hide/show choices forward is the more useful default than losing them.
  const [hiddenGroups,setHiddenGroups]=useState(() => new Set());
  const toggleGroup = (name) => setHiddenGroups(prev => {
    const next = new Set(prev);
    if (next.has(name)) next.delete(name); else next.add(name);
    return next;
  });
  const value=useMemo(()=>({params,setParams,hiddenGroups,setHiddenGroups,toggleGroup}),[params,hiddenGroups]);
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export const useApp = () => useContext(AppContext);
