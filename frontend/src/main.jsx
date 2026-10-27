import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import AccessGate from './AccessGate'
import './styles.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode><AccessGate>{(onSwitchUser, customer) => <App onSwitchUser={onSwitchUser} customer={customer} />}</AccessGate></React.StrictMode>,
)

