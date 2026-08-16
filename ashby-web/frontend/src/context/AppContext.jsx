import { createContext, useContext, useMemo, useState } from 'react';
const AppContext = createContext(null);
export function AppProvider({ children }) {
  const [params, setParams] = useState({ x_axis:'Density_kg_m3', y_axis:'Youngs_Modulus_GPa', criterion:'E_over_rho', mode:'high' });
  const value = useMemo(() => ({ params, setParams }), [params]);
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}
export const useApp = () => useContext(AppContext);
