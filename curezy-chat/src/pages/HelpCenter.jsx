import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Search, Book, MessageCircle, CreditCard, Settings } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function HelpCenter() {
    return (
        <div className="relative min-h-screen bg-[#050510] text-white overflow-hidden py-24 px-6 md:px-12 font-sans">
            {/* Ambient Base */}
            <div className="fixed inset-0 pointer-events-none opacity-20" style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

            <div className="max-w-4xl mx-auto relative z-10">
                <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-12 transition-colors">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Home
                </Link>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.6 }}
                    className="text-center mb-16"
                >
                    <h1 className="text-4xl md:text-5xl font-bold tracking-tight mb-6 text-white">How can we help you?</h1>
                    <div className="relative max-w-2xl mx-auto">
                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                        <input
                            type="text"
                            placeholder="Search for articles, guides, and troubleshooting..."
                            className="w-full bg-white/5 border border-white/10 rounded-full py-4 pl-12 pr-6 text-white placeholder-gray-500 focus:outline-none focus:border-[#4D4DFF] focus:bg-white/10 transition-all shadow-xl"
                        />
                    </div>
                </motion.div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Card 1 */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="bg-white/5 border border-white/10 p-8 rounded-3xl hover:bg-white/10 transition-colors cursor-pointer group">
                        <Book className="w-8 h-8 text-[#FF7A00] mb-4 group-hover:scale-110 transition-transform" />
                        <h3 className="text-xl font-bold mb-2">Getting Started Guides</h3>
                        <p className="text-gray-400 text-sm">Learn the basics of setting up your clinic and importing patient data into the AI Council.</p>
                    </motion.div>

                    {/* Card 2 */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="bg-white/5 border border-white/10 p-8 rounded-3xl hover:bg-white/10 transition-colors cursor-pointer group">
                        <MessageCircle className="w-8 h-8 text-[#4D4DFF] mb-4 group-hover:scale-110 transition-transform" />
                        <h3 className="text-xl font-bold mb-2">Troubleshooting</h3>
                        <p className="text-gray-400 text-sm">Fix common errors regarding DICOM uploads, voice transcribing timeouts, and EHR syncs.</p>
                    </motion.div>

                    {/* Card 3 */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="bg-white/5 border border-white/10 p-8 rounded-3xl hover:bg-white/10 transition-colors cursor-pointer group">
                        <CreditCard className="w-8 h-8 text-green-400 mb-4 group-hover:scale-110 transition-transform" />
                        <h3 className="text-xl font-bold mb-2">Billing & Plans</h3>
                        <p className="text-gray-400 text-sm">Manage your Pro/Enterprise subscription, custom model requests, and invoicing.</p>
                    </motion.div>

                    {/* Card 4 */}
                    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.4 }} className="bg-white/5 border border-white/10 p-8 rounded-3xl hover:bg-white/10 transition-colors cursor-pointer group">
                        <Settings className="w-8 h-8 text-purple-400 mb-4 group-hover:scale-110 transition-transform" />
                        <h3 className="text-xl font-bold mb-2">API Documentation</h3>
                        <p className="text-gray-400 text-sm">Integrate the Council Engine webhook directly into your proprietary hospital software.</p>
                    </motion.div>
                </div>

                <div className="mt-16 text-center border-t border-white/10 pt-10">
                    <p className="text-gray-400 mb-4">Can't find what you're looking for?</p>
                    <a href="mailto:support@curezy.com" className="inline-flex items-center gap-2 px-6 py-2.5 bg-white text-black rounded-full font-bold hover:scale-105 transition-transform">
                        Contact Support
                    </a>
                </div>
            </div>
        </div>
    );
}
