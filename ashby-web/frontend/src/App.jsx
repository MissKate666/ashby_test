import React from 'react';import {createRoot} from 'react-dom/client';import './index.css';import {AppProvider,useApp} from './context/AppContext';import {useDiagramData} from './hooks/useDiagramData';import Layout from './components/Layout/Layout';import AshbyDiagram from './components/Diagram/AshbyDiagram';
function Page(){const {params,hiddenGroups}=useApp();const state=useDiagramData(params);const items=state.items.length?state.items:[{condition:params.condition,label:'Диаграмма',data:state.data}];
  // suitable_count/total_count come from the backend over ALL groups; hiding a
  // group is purely a client-side display filter (see AppContext.jsx), so those
  // points must be subtracted here rather than by re-querying the backend.
  const visiblePoints=state.data?.points?.filter(p=>!hiddenGroups.has(p.group));
  const summary=state.data&&visiblePoints?{...state.data,suitable_count:visiblePoints.filter(p=>p.is_suitable).length,total_count:visiblePoints.length}:state.data;
  return <Layout summary={summary}><div className="h-full min-h-0 overflow-y-auto pr-1"><div className={`grid h-full auto-rows-[100%] gap-4 ${items.length>1?'xl:grid-cols-2':''}`}>{items.map(item=><AshbyDiagram key={item.condition} condition={item.condition} title={item.label} data={item.data} loading={state.loading} error={state.error}/>)}</div></div></Layout>}
createRoot(document.getElementById('root')).render(<React.StrictMode><AppProvider><Page/></AppProvider></React.StrictMode>);
