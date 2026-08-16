import React from 'react';import {createRoot} from 'react-dom/client';import './index.css';import {AppProvider,useApp} from './context/AppContext';import {useDiagramData} from './hooks/useDiagramData';import Layout from './components/Layout/Layout';import AshbyDiagram from './components/Diagram/AshbyDiagram';
function Page(){const {params}=useApp();const state=useDiagramData(params);return <Layout summary={state.data}><AshbyDiagram {...state}/></Layout>}
createRoot(document.getElementById('root')).render(<React.StrictMode><AppProvider><Page/></AppProvider></React.StrictMode>);
