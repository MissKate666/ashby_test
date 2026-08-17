import * as d3 from 'd3';
import {useEffect,useRef} from 'react';
import './diagramStyles.css';

const materialPalette=['rgb(22, 19, 31)','rgb(74, 63, 75)','rgb(128, 108, 121)','rgb(193, 160, 172)'];
const groupHue=i=>(318+i*47)%360;
const groupColor=i=>`hsl(${groupHue(i)} 28% 56%)`;
const hash=value=>String(value).split('').reduce((a,c)=>a+c.charCodeAt(0),0);
const subgroupColor=(d,i,groupIndex)=>`hsl(${(groupHue(groupIndex)+(hash(d.subgroup||i)%5-2)*7+360)%360} 26% 61%)`;
const colorFor=(d,i)=>materialPalette[Math.abs(String(d.id||d.name||i).split('').reduce((a,c)=>a+c.charCodeAt(0),0))%materialPalette.length];

function blobPath(polygon,x,y,amplitude=10){
  if(!polygon?.length)return null;
  const stride=Math.max(1,Math.ceil(polygon.length/18));
  const anchors=polygon.filter((_,index)=>index%stride===0).map(point=>[x(point[0]),y(point[1])]);
  const center=[d3.mean(anchors,d=>d[0]),d3.mean(anchors,d=>d[1])];
  const controls=[];
  anchors.forEach(([sx,sy],index)=>{
    const [ex,ey]=anchors[(index+1)%anchors.length];
    controls.push([sx,sy]);
    controls.push([(sx+ex)/2,(sy+ey)/2]);
  });
  const points=controls.map(([px,py],index)=>{
    const dx=px-center[0];
    const dy=py-center[1];
    const length=Math.hypot(dx,dy)||1;
    const lobe=1+Math.sin(index*.7+polygon.length)*.18;
    return [px+(dx/length)*amplitude*lobe,py+(dy/length)*amplitude*lobe];
  });
  return d3.line().curve(d3.curveBasisClosed)(points);
}

export function useDiagram(svgRef,tipRef,data,size,setParams){const transformRef=useRef(d3.zoomIdentity);useEffect(()=>{if(!data||!size.width||!size.height)return;const svg=d3.select(svgRef.current);svg.selectAll('*').remove();const margin={top:24,right:28,bottom:56,left:72},w=size.width-margin.left-margin.right,h=size.height-margin.top-margin.bottom;const root=svg.attr('viewBox',[0,0,size.width,size.height]).classed('ashby-svg',true);const x0=d3.scaleLog().domain(data.x_range).range([0,w]).nice();const y0=d3.scaleLog().domain(data.y_range).range([h,0]).nice();const g=root.append('g').attr('transform',`translate(${margin.left},${margin.top})`);const plot=g.append('g').attr('clip-path','url(#clip)');const defs=root.append('defs');defs.append('clipPath').attr('id','clip').append('rect').attr('x',margin.left).attr('y',margin.top).attr('width',w).attr('height',h);const groupClips=defs.append('g').attr('data-layer','group-clips');const gx=g.append('g').attr('class','axis').attr('transform',`translate(0,${h})`),gy=g.append('g').attr('class','axis');const gridX=g.append('g').attr('class','grid').attr('transform',`translate(0,${h})`),gridY=g.append('g').attr('class','grid');g.append('text').attr('x',w/2).attr('y',h+45).attr('text-anchor','middle').attr('font-weight',800).text('Плотность, кг/м³');g.append('text').attr('transform','rotate(-90)').attr('x',-h/2).attr('y',-52).attr('text-anchor','middle').attr('font-weight',800).text(data.points?.[0]?.y===data.points?.[0]?.strength?'Прочность, МПа':'Модуль Юнга, ГПа');const group=plot.append('g'),sub=plot.append('g'),pts=plot.append('g'),lineG=plot.append('g');function render(t=transformRef.current){transformRef.current=t;const x=t.rescaleX(x0),y=t.rescaleY(y0);gx.call(d3.axisBottom(x).ticks(8,'.1~g'));gy.call(d3.axisLeft(y).ticks(8,'.1~g'));gridX.call(d3.axisBottom(x).ticks(8).tickSize(-h).tickFormat(''));gridY.call(d3.axisLeft(y).ticks(8).tickSize(-w).tickFormat(''));const groupShapes=data.groups.filter(d=>d.kind==='group');const groupIndex=new Map(groupShapes.map((d,i)=>[d.id,i]));groupClips.selectAll('clipPath').data(groupShapes,d=>d.id).join('clipPath').attr('id',d=>`group-clip-${d.id}`).selectAll('path').data(d=>[d]).join('path').attr('d',d=>blobPath(d.polygon,x,y,9));group.selectAll('path').data(groupShapes,d=>d.id).join('path').attr('class','group-shape group-blob').attr('fill',(_,i)=>groupColor(i)).attr('fill-opacity',.3).attr('stroke',(_,i)=>groupColor(i)).attr('stroke-opacity',.86).attr('stroke-width',2.4).attr('stroke-linejoin','round').attr('stroke-linecap','round').attr('d',d=>blobPath(d.polygon,x,y,9));sub.selectAll('path').data(data.groups.filter(d=>d.kind==='subgroup'),d=>`${d.id}-${d.subgroup}`).join('path').attr('class','group-shape subgroup-blob').attr('clip-path',d=>`url(#group-clip-${d.id})`).attr('fill',(d,i)=>subgroupColor(d,i,groupIndex.get(d.id)??i)).attr('fill-opacity',.45).attr('stroke',(d,i)=>subgroupColor(d,i,groupIndex.get(d.id)??i)).attr('stroke-opacity',.6).attr('stroke-width',1.2).attr('stroke-linejoin','round').attr('stroke-linecap','round').attr('d',d=>blobPath(d.polygon,x,y,4));pts.selectAll('circle').data(data.points,d=>d.name).join('circle').attr('class',d=>`material-point ${d.is_suitable?'':'dim'}`).attr('r',d=>d.is_suitable?5:3.5).attr('fill',(d,i)=>d.is_suitable?colorFor(d,i+31):'rgb(128, 108, 121)').attr('cx',d=>x(d.x)).attr('cy',d=>y(d.y)).on('mousemove',(ev,d)=>{const tip=tipRef.current;tip.hidden=false;tip.style.left=ev.clientX+12+'px';tip.style.top=ev.clientY+12+'px';tip.innerHTML=`<b>${d.name}</b><br>${d.group} / ${d.subgroup}<br>ρ=${d.x}, y=${d.y}`}).on('mouseleave',()=>tipRef.current.hidden=true);if(data.condition_line){lineG.selectAll('path').data([data.condition_line]).join('path').attr('class','condition-line').attr('fill','none').attr('d',d3.line().x((_,i)=>x(data.condition_line.x[i])).y(v=>y(v))(data.condition_line.y)).call(d3.drag().on('drag',(ev)=>{const domainY=y.invert(ev.y);const domainX=x.invert(Math.max(1,Math.min(w,ev.x)));setParams(p=>({...p,intercept:Math.log10(domainY)-data.condition_line.slope*Math.log10(domainX)}))}))}}render();root.call(d3.zoom().scaleExtent([.5,40]).on('zoom',e=>render(e.transform)));window.__ashbyZoom=(factor)=>root.transition().call(d3.zoom().scaleBy,factor)},[data,size.width,size.height,setParams])}
