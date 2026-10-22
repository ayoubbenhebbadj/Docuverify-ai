import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import './index.css'
import Layout from './components/Layout'
import Overview from './pages/Overview'
import Documents from './pages/Documents'
import Operations from './pages/Operations'
import Verification from './pages/Verification'
import Reports from './pages/Reports'
import Rules from './pages/Rules'
import SettingsPage from './pages/Settings'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode><BrowserRouter>
    <Routes><Route element={<Layout />}>
      <Route index element={<Overview />} />
      <Route path="documents" element={<Documents />} />
      <Route path="operations" element={<Operations />} />
      <Route path="verification" element={<Verification />} />
      <Route path="verification/:id" element={<Verification />} />
      <Route path="reports" element={<Reports />} />
      <Route path="rules" element={<Rules />} />
      <Route path="settings" element={<SettingsPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Route></Routes>
    <Toaster position="top-right" />
  </BrowserRouter></React.StrictMode>)
