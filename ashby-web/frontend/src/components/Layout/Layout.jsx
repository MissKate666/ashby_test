import React, {useState} from 'react';
import Header from './Header';
import ControlsPanel from '../Controls/ControlsPanel';
import MaterialsPreviewModal from '../Preview/MaterialsPreviewModal';

export default function Layout({children,summary,searchPoints,multiChart}){const [open,setOpen]=useState(false);const [previewOpen,setPreviewOpen]=useState(false);return <div className="flex h-dvh flex-col gap-4 p-3 md:p-6"><Header onMenu={()=>setOpen(true)} summary={summary} searchPoints={searchPoints}/><main className="grid min-h-0 flex-1 gap-4 md:grid-cols-[16rem_minmax(0,1fr)] lg:grid-cols-[22rem_minmax(0,1fr)]"><ControlsPanel open={open} onClose={()=>setOpen(false)} summary={summary} onPreview={()=>setPreviewOpen(true)} multiChart={multiChart}/>{children}</main><MaterialsPreviewModal open={previewOpen} onClose={()=>setPreviewOpen(false)} points={summary?.points}/></div>}
