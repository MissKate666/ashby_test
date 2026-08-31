import React, {createContext, useContext, useEffect, useMemo, useRef, useState} from 'react';

const AppContext = createContext(null);

const defaultCondition = 'stiffness';
const MAX_HISTORY = 30;

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
  // Shared here (rather than inline where the button lives) since the sync toggle
  // is a single cross-chart setting: every chart's settings menu renders the same
  // "≡" button reading/writing the same params.syncLines, not a per-chart control.
  const toggleSyncLines = () => setParams(p => {
    const syncLines = !p.syncLines;
    if (syncLines) return {...p, syncLines};
    const current = p.conditions?.length ? p.conditions : [p.condition].filter(Boolean);
    const intercepts = Object.fromEntries(current.map(condition => [condition, p.intercepts?.[condition] ?? p.intercept]));
    return {...p, syncLines, intercept: null, intercepts};
  });
  // Undo/Redo: tracks the criterion, preference, line position and axis bounds --
  // everything in `params` + `axisBoundsByCondition` -- but deliberately NOT
  // hiddenGroupsByCondition (legend visibility is a pure display filter, not an
  // "action" worth stepping back through). A single effect watching both pieces
  // of state is the one funnel every change already flows through (criterion
  // picks, preference, axis-bound edits, index input/reset, line drags, sync
  // toggling), so nothing needs to call into undo/redo directly.
  const [undoStack,setUndoStack]=useState([]);
  const [redoStack,setRedoStack]=useState([]);
  const currentRef=useRef(null);
  const restoringRef=useRef(false);
  useEffect(()=>{
    const key=JSON.stringify({params,axisBoundsByCondition});
    if(restoringRef.current){
      currentRef.current={key,params,axisBoundsByCondition};
      restoringRef.current=false;
      return;
    }
    const prev=currentRef.current;
    if(prev&&prev.key!==key){
      setUndoStack(stack=>{
        const next=[...stack,{params:prev.params,axisBoundsByCondition:prev.axisBoundsByCondition}];
        return next.length>MAX_HISTORY?next.slice(next.length-MAX_HISTORY):next;
      });
      setRedoStack([]);
    }
    currentRef.current={key,params,axisBoundsByCondition};
  },[params,axisBoundsByCondition]);
  const undo=()=>setUndoStack(stack=>{
    if(!stack.length||!currentRef.current)return stack;
    const prevState=stack[stack.length-1];
    setRedoStack(r=>{
      const next=[...r,{params:currentRef.current.params,axisBoundsByCondition:currentRef.current.axisBoundsByCondition}];
      return next.length>MAX_HISTORY?next.slice(next.length-MAX_HISTORY):next;
    });
    restoringRef.current=true;
    setParams(prevState.params);
    setAxisBoundsByCondition(prevState.axisBoundsByCondition);
    return stack.slice(0,-1);
  });
  const redo=()=>setRedoStack(stack=>{
    if(!stack.length||!currentRef.current)return stack;
    const nextState=stack[stack.length-1];
    setUndoStack(u=>{
      const next=[...u,{params:currentRef.current.params,axisBoundsByCondition:currentRef.current.axisBoundsByCondition}];
      return next.length>MAX_HISTORY?next.slice(next.length-MAX_HISTORY):next;
    });
    restoringRef.current=true;
    setParams(nextState.params);
    setAxisBoundsByCondition(nextState.axisBoundsByCondition);
    return stack.slice(0,-1);
  });
  const value=useMemo(()=>({params,setParams,hiddenGroupsByCondition,setHiddenGroupsFor,toggleGroup,axisBoundsByCondition,setAxisBoundsFor,toggleSyncLines,undo,redo,canUndo:undoStack.length>0,canRedo:redoStack.length>0}),[params,hiddenGroupsByCondition,axisBoundsByCondition,undoStack,redoStack]);
  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export const useApp = () => useContext(AppContext);
