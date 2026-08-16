import { useEffect, useState } from 'react';
export function useResizeObserver(ref){const [size,setSize]=useState({width:800,height:500});useEffect(()=>{if(!ref.current)return;const ro=new ResizeObserver(([e])=>setSize({width:e.contentRect.width,height:e.contentRect.height}));ro.observe(ref.current);return()=>ro.disconnect()},[ref]);return size;}
