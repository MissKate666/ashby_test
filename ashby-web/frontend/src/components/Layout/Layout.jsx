import React, {useState} from 'react';
import Header from './Header';
import ControlsPanel from '../Controls/ControlsPanel';

export default function Layout({children,summary}){const [open,setOpen]=useState(false);return <div className="flex h-screen flex-col gap-4 p-3 md:p-6"><Header onMenu={()=>setOpen(true)}/><main className="grid min-h-0 flex-1 gap-4 lg:grid-cols-[22rem_minmax(0,1fr)]"><ControlsPanel open={open} onClose={()=>setOpen(false)} summary={summary}/>{children}</main></div>}
