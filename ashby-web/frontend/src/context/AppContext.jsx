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
  const value=useMemo(()=>({params,setParams}),[params]);
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export const useApp = () => useContext(AppContext);
