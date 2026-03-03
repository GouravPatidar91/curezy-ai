import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, ShieldCheck } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function PrivacyPolicy() {
    return (
        <div className="relative min-h-screen bg-[#050510] text-gray-300 py-24 px-6 md:px-12 font-sans font-medium">
            <div className="fixed inset-0 pointer-events-none opacity-20" style={{ backgroundImage: 'radial-gradient(circle, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

            <div className="max-w-3xl mx-auto relative z-10">
                <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white mb-12 transition-colors">
                    <ArrowLeft className="w-4 h-4" />
                    Back to Home
                </Link>

                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}>
                    <div className="flex items-center gap-4 mb-8">
                        <div className="w-12 h-12 bg-[#4D4DFF]/10 border border-[#4D4DFF]/20 rounded-xl flex items-center justify-center">
                            <ShieldCheck className="w-6 h-6 text-[#4D4DFF]" />
                        </div>
                        <h1 className="text-4xl font-bold tracking-tight text-white">Privacy Policy</h1>
                    </div>

                    <div className="prose prose-invert max-w-none space-y-6">
                        <p className="text-lg leading-relaxed text-gray-400">
                            Effective Date: January 1, 2024
                        </p>

                        <div className="bg-white/5 border border-white/10 p-6 md:p-10 rounded-3xl space-y-8">
                            <section>
                                <h2 className="text-xl font-bold text-white mb-3 flex items-center gap-2"><div className="w-1.5 h-1.5 bg-[#FF7A00] rounded-full" /> 1. Information We Collect</h2>
                                <p className="leading-relaxed text-gray-400 text-sm">
                                    When you use Curezy AI, we may collect minimal personal information (such as your name and email address) when you sign up for early access or contact support. Additionally, any medical information, symptoms, or images (DICOM/JPEG) you upload to the AI Council engine are temporarily processed in memory to generate the debate output.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-xl font-bold text-white mb-3 flex items-center gap-2"><div className="w-1.5 h-1.5 bg-[#FF7A00] rounded-full" /> 2. Data Encryption & HIPAA Compliance</h2>
                                <p className="leading-relaxed text-gray-400 text-sm">
                                    Privacy is paramount in medical technology. All data transmitted to our servers is encrypted in transit using TLS 1.3. For Enterprise and Clinical users, we offer a strict zero-retention policy where absolutely no patient data is logged or used to train future foundation models.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-xl font-bold text-white mb-3 flex items-center gap-2"><div className="w-1.5 h-1.5 bg-[#FF7A00] rounded-full" /> 3. How We Use Data</h2>
                                <p className="leading-relaxed text-gray-400 text-sm">
                                    We use the information we collect to provide, maintain, and improve the AI diagnostic engine, process your requests, and communicate with you regarding updates or technical support.
                                </p>
                            </section>

                            <section>
                                <h2 className="text-xl font-bold text-white mb-3 flex items-center gap-2"><div className="w-1.5 h-1.5 bg-[#FF7A00] rounded-full" /> 4. Sharing of Information</h2>
                                <p className="leading-relaxed text-gray-400 text-sm">
                                    We do not sell, trade, or rent your personal identification information to others. We may share generic aggregated demographic information not linked to any personal identification regarding visitors with our business partners and trusted affiliates.
                                </p>
                            </section>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
