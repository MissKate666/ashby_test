import React,{useMemo} from 'react';import {createRoot} from 'react-dom/client';import './index.css';import {AppProvider,useApp} from './context/AppContext';import {useDiagramData} from './hooks/useDiagramData';import Layout from './components/Layout/Layout';import AshbyDiagram from './components/Diagram/AshbyDiagram';
const EMPTY_SET=new Set();
function Page(){const {params,hiddenGroupsByCondition,axisBoundsByCondition}=useApp();const state=useDiagramData(params,axisBoundsByCondition);const items=state.items.length?state.items:[{condition:params.condition,label:'Диаграмма',data:state.data}];
  // suitable_count/total_count come from the backend over ALL groups; hiding a
  // group is purely a client-side display filter (see AppContext.jsx), so those
  // points must be subtracted here rather than by re-querying the backend. The
  // control panel's counter and the preview table both reflect the FIRST chart
  // (state.data), so they use that chart's own hidden-groups entry -- each other
  // chart keeps its own independent set, unaffected by this.
  const firstHiddenGroups=hiddenGroupsByCondition[items[0]?.condition]??EMPTY_SET;
  const visiblePoints=state.data?.points?.filter(p=>!firstHiddenGroups.has(p.group));
  const summary=state.data&&visiblePoints?{...state.data,points:visiblePoints,suitable_count:visiblePoints.filter(p=>p.is_suitable).length,total_count:visiblePoints.length}:state.data;
  // The header search box is global (one query, all open charts), so unlike
  // `summary` above it must not be scoped to just the first chart's hidden
  // groups -- otherwise a material hidden on chart #2 but visible on chart #1
  // (each chart has its own independent hiddenGroups, see AppContext.jsx)
  // could be miscounted. Union every currently-open chart's own visible points,
  // deduped by material name, so "Found: X of Y" matches what's actually
  // visible somewhere on screen.
  const searchPoints=useMemo(()=>{
    const seen=new Map();
    items.forEach(item=>{
      const hidden=hiddenGroupsByCondition[item.condition]??EMPTY_SET;
      (item.data?.points||[]).forEach(p=>{if(!hidden.has(p.group)&&!seen.has(p.name))seen.set(p.name,p)});
    });
    return Array.from(seen.values());
  },[items,hiddenGroupsByCondition]);
  return <Layout summary={summary} searchPoints={searchPoints} multiChart={items.length>1}><div className="h-full min-h-0 overflow-y-auto pr-1"><div className={`grid h-full auto-rows-[100%] gap-4 ${items.length>1?'xl:grid-cols-2':''}`}>{items.map(item=><AshbyDiagram key={item.condition} condition={item.condition} title={item.label} data={item.data} loading={state.loading} error={state.error}/>)}</div></div></Layout>}
createRoot(document.getElementById('root')).render(<React.StrictMode><AppProvider><Page/></AppProvider></React.StrictMode>);
