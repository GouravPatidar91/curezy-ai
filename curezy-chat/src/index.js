import React from 'react'
import ReactDOM from 'react-dom/client'

// Suppress the benign Supabase "Lock broken" AbortError in development
window.addEventListener('unhandledrejection', (event) => {
    if (event.reason && event.reason.message && event.reason.message.includes('Lock broken by another request')) {
        event.preventDefault();
        console.warn('Ignored benign Supabase auth lock error.');
    }
});

window.addEventListener('error', (event) => {
    if (event.message && event.message.includes('Lock broken by another request')) {
        event.preventDefault();
        console.warn('Ignored benign Supabase auth lock error.');
    }
});
import './index.css'
import App from './App'

const root = ReactDOM.createRoot(document.getElementById('root'))
root.render(<App />)