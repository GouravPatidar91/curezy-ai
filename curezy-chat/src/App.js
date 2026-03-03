import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Landing from './pages/Landing'
import Chat from './pages/Chat'
import ApiKeys from './pages/ApiKeys'
import FineTune from './pages/FineTune'
import BenchmarkDashboard from './pages/BenchmarkDashboard'
// New Footer Pages
import Documentation from './pages/Documentation'
import HelpCenter from './pages/HelpCenter'
import MedicalDisclaimers from './pages/MedicalDisclaimers'
import AboutUs from './pages/AboutUs'
import Careers from './pages/Careers'
import PrivacyPolicy from './pages/PrivacyPolicy'
import TermsOfService from './pages/TermsOfService'

function PrivateRoute({ children }) {
    const { user } = useAuth()
    return user ? children : <Navigate to="/" replace />
}

function PublicRoute({ children }) {
    const { user } = useAuth()
    return user ? <Navigate to="/chat" replace /> : children
}

function AppRoutes() {
    return (
        <Routes>
            <Route path="/" element={<PublicRoute><Landing /></PublicRoute>} />
            <Route path="/chat" element={<PrivateRoute><Chat /></PrivateRoute>} />
            <Route path="/apikeys" element={<PrivateRoute><ApiKeys /></PrivateRoute>} />
            <Route path="/finetune" element={<PrivateRoute><FineTune /></PrivateRoute>} />
            <Route path="/benchmark" element={<PrivateRoute><BenchmarkDashboard /></PrivateRoute>} />

            {/* Corporate & Resource Routes (Public) */}
            <Route path="/documentation" element={<Documentation />} />
            <Route path="/help" element={<HelpCenter />} />
            <Route path="/medical-disclaimer" element={<MedicalDisclaimers />} />
            <Route path="/about" element={<AboutUs />} />
            <Route path="/careers" element={<Careers />} />
            <Route path="/privacy" element={<PrivacyPolicy />} />
            <Route path="/terms" element={<TermsOfService />} />

            <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
    )
}

export default function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <AppRoutes />
            </AuthProvider>
        </BrowserRouter>
    )
}