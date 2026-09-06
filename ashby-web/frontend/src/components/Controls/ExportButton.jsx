import React from 'react';
import {exportUrl} from '../../services/api';import {useApp} from '../../context/AppContext';
export default function ExportButton(){const {params,axisBoundsByCondition}=useApp();const bounds=axisBoundsByCondition[params.condition]||{};const body={...params,...bounds};return <div className="grid grid-cols-2 gap-2"><a className="btn-secondary text-center" href={exportUrl('csv',body)}>CSV</a><a className="btn-primary text-center" href={exportUrl('excel',body)}>Excel</a></div>}
