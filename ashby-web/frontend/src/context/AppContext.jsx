import React, {createContext, useContext, useMemo, useState} from 'react';
const AppContext = createContext(null);
export function AppProvider({children}){const [params,setParams]=useState({condition:'stiffness',preference:'high',x_min:'',x_max:'',y_min:'',y_max:'',intercept:null}); const value=useMemo(()=>({params,setParams}),[params]); return <AppContext.Provider value={value}>{children}</AppContext.Provider>}
export const useApp = () => useContext(AppContext);
