import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { TopologyContextProvider } from './context/TopologyContext.jsx'
import App from './App.jsx'
import './index.css'

createRoot(document.getElementById('root')).render(
    <StrictMode>
        <TopologyContextProvider>
            <App />
        </TopologyContextProvider>
    </StrictMode>,
)