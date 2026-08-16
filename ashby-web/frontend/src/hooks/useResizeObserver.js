import {useEffect,useState} from 'react';
export function useResizeObserver(ref){const [rect,setRect]=useState({width:0,height:0});useEffect(()=>{if(!ref.current)return;const ro=new ResizeObserver(([e])=>setRect(e.contentRect));ro.observe(ref.current);return()=>ro.disconnect()},[ref]);return rect}
