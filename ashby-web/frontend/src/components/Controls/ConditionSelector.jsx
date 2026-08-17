import React from 'react';
import {useApp} from '../../context/AppContext';

const conditionOptions=[
  ['stiffness','Лёгкость (E/ρ)'],
  ['strength','Прочность (σ/ρ)'],
  ['bending','Изгиб (√E/ρ)'],
];

export default function ConditionSelector(){const {params,setParams}=useApp();const selected=params.conditions?.length?params.conditions:[params.condition].filter(Boolean);const toggle=condition=>setParams(p=>{const current=p.conditions?.length?p.conditions:[p.condition].filter(Boolean);const next=current.includes(condition)?current.filter(v=>v!==condition):[...current,condition];const conditions=next.length?next:[condition];return {...p,conditions,condition:conditions[0],intercept:null,intercepts:{}}});const set=(k,v)=>setParams(p=>({...p,[k]:v,intercept:k==='preference'?null:p.intercept,intercepts:k==='preference'?{}:p.intercepts}));return <div className="grid gap-3"><div><p className="panel-label mb-2">Критерии эффективности</p><div className="grid gap-2">{conditionOptions.map(([value,label])=><label key={value} className="flex items-center gap-2 rounded-xl bg-[rgba(240,217,228,0.5)] px-3 py-2 text-sm font-bold text-[rgb(22,19,31)]"><input type="checkbox" checked={selected.includes(value)} onChange={()=>toggle(value)}/><span>{label}</span></label>)}</div></div><label className="flex items-center gap-2 rounded-xl bg-[rgba(240,217,228,0.5)] px-3 py-2 text-sm font-bold text-[rgb(22,19,31)]"><input type="checkbox" checked={params.syncLines} onChange={e=>setParams(p=>({...p,syncLines:e.target.checked,intercept:null,intercepts:{}}))}/><span>Двигать линии синхронно</span></label><label className="panel-label">Подходит<select className="panel-input mt-1" value={params.preference} onChange={e=>set('preference',e.target.value)}><option value="high">Высокое значение</option><option value="low">Низкое значение</option></select></label></div>}
