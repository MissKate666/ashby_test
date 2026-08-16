import { exportUrl } from '../../services/api';
export default function ExportButton({type,params,children}){return <a className="btn bg-slate-900 text-white text-center" href={exportUrl(type,params)}>{children}</a>}
