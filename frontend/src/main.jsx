import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import AccessGate from './AccessGate'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><AccessGate>{(onSwitchUser, customer, initialAdminPreview) => <App onSwitchUser={onSwitchUser} customer={customer} initialAdminPreview={initialAdminPreview} />}</AccessGate></React.StrictMode>,
)

