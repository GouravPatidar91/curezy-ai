import React from 'react';
import { motion } from 'framer-motion';
import { FileText, ArrowLeft, Mail } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Documentation() {
    return (
        <div className="relative min-h-screen bg-[#050510] text-white flex flex-col items-center justify-center p-6 text-center overflow-hidden">
            {/* Ambient Starfield / Noise */}
            <div className="absolute inset-0 pointer-events-none opacity-20" style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

            <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                transition={{ duration: 0.5 }}
                className="relative z-10 max-w-lg w-full bg-white/5 backdrop-blur-3xl border border-white/10 rounded-3xl p-10 md:p-14 shadow-2xl overflow-hidden"
            >
                <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-[#4D4DFF] to-[#FF7A00]" />

                <div className="w-20 h-20 bg-white/5 border border-white/10 rounded-2xl flex items-center justify-center mx-auto mb-8 shadow-inner">
                    <FileText className="w-10 h-10 text-[#4D4DFF]" />
                </div>

                <h1 className="text-3xl font-bold tracking-tight mb-4 text-white">Classified Documentation</h1>
                <p className="text-gray-400 text-sm leading-relaxed mb-8">
                    The core API and internal system architecture documentation for the Curezy AI engine is restricted. Please contact the administrator to request an access token or an API developer key.
                </p>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                    <a href="mailto:admin@curezy.in" className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 bg-[#4D4DFF] hover:bg-[#3b3bdf] text-white rounded-xl font-medium transition-colors">
                        <Mail className="w-4 h-4" />
                        Contact Admin
                    </a>
                    <Link to="/" className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 bg-white/10 hover:bg-white/20 text-white rounded-xl font-medium transition-colors">
                        <ArrowLeft className="w-4 h-4" />
                        Go Back
                    </Link>
                </div>
            </motion.div>
        </div>
    );
}
