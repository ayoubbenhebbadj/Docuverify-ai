import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import Layout from './components/Layout'
import { AnalysisProvider } from './state/AnalysisContext'
import Overview from './pages/Overview'
import NewAnalysis from './pages/NewAnalysis'
import Results from './pages/Results'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><BrowserRouter><AnalysisProvider>
    <Routes><Route element={<Layout />}><Route index element={<Overview />} /><Route path="analysis" element={<NewAnalysis />} /><Route path="results" element={<Results />} /><Route path="*" element={<Navigate to="/" replace />} /></Route></Routes>
  </AnalysisProvider></BrowserRouter></React.StrictMode>)
