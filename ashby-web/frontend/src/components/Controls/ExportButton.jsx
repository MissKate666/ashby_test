import React from 'react';
import {exportUrl} from '../../services/api';import {useApp} from '../../context/AppContext';
export default function ExportButton(){const {params}=useApp();return <div className="grid grid-cols-2 gap-2"><a className="btn-secondary text-center" href={exportUrl('csv',params)}>CSV</a><a className="btn-primary text-center" href={exportUrl('excel',params)}>Excel</a></div>}
