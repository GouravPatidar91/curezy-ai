import { X, Phone, MapPin, Clock, AlertTriangle, FileSearch, ClipboardList, ChevronRight } from 'lucide-react'

export default function DoctorReferral({ analysis, onClose }) {
    const isUrgent = analysis?.doctor_review_required || false
    const conditions = analysis?.top_3_conditions || []
    const topCondition = conditions[0]?.condition || 'your symptoms'

    const specialties = {
        'Pneumonia': 'Pulmonologist',
        'Chronic Kidney Disease': 'Nephrologist',
        'Heart Failure': 'Cardiologist',
        'Iron Deficiency Anemia': 'Hematologist',
        'Type 2 Diabetes': 'Endocrinologist',
        'Hypertension': 'Cardiologist',
        'Tuberculosis': 'Pulmonologist',
        'Viral Infection': 'General Physician',
        'Fever': 'General Physician',
        'default': 'General Physician',
    }

    const getSpecialty = () => {
        for (const [key, spec] of Object.entries(specialties)) {
            if (topCondition.toLowerCase().includes(key.toLowerCase())) return spec
        }
        return specialties.default
    }

    // Categorize missing data suggestions
    const rawSuggestions = analysis?.missing_data_suggestions || []
    const clinicalTests = rawSuggestions.filter(s => 
        s.toLowerCase().includes('report') || 
        s.toLowerCase().includes('test') || 
        s.toLowerCase().includes('scan') ||
        s.toLowerCase().includes('level')
    )
    const clarifications = rawSuggestions.filter(s => !clinicalTests.includes(s))

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 transition-all animate-in fade-in duration-300">
            <div className="bg-white rounded-[32px] shadow-2xl w-full max-w-md overflow-hidden animate-in zoom-in-95 duration-300">
                
                {/* Header Section */}
                <div className={`p-7 relative ${isUrgent ? 'bg-red-50' : 'bg-primary-50'}`}>
                    <button 
                        onClick={onClose} 
                        className="absolute top-6 right-6 p-2 rounded-full bg-white/50 hover:bg-white text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X size={18} />
                    </button>
                    
                    <div className="flex items-center gap-3 mb-4">
                        <div className={`w-10 h-10 rounded-2xl flex items-center justify-center ${isUrgent ? 'bg-red-100 text-red-600' : 'bg-primary-100 text-primary-600'}`}>
                            {isUrgent ? <AlertTriangle size={22} /> : <ClipboardList size={22} />}
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-gray-900 tracking-tight">
                                {isUrgent ? 'Urgent Consultation' : 'Clinical Referral'}
                            </h2>
                            <p className={`text-xs font-medium uppercase tracking-wider ${isUrgent ? 'text-red-500' : 'text-primary-500'}`}>
                                Patient Brief Generated
                            </p>
                        </div>
                    </div>
                    
                    <p className="text-[13.5px] leading-relaxed text-gray-600 pr-8">
                        {isUrgent
                            ? 'Based on your markers, we recommend a priority clinical review within 24 hours.'
                            : 'This brief is prepared for your doctor to accelerate your diagnostic evaluation.'
                        }
                    </p>
                </div>

                {/* Main Content Area */}
                <div className="p-7 pt-5 space-y-6 max-h-[60vh] overflow-y-auto custom-scrollbar">
                    
                    {/* Recommended Specialist Card */}
                    <div className="bg-gray-50 border border-gray-100 rounded-2xl p-5 group hover:border-primary-100 transition-colors">
                        <div className="flex items-center justify-between mb-2.5">
                            <span className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.1em]">Target Specialist</span>
                            <span className="px-2 py-0.5 bg-primary-100 text-primary-700 text-[10px] font-bold rounded-full">Primary Match</span>
                        </div>
                        <p className="text-lg font-extrabold text-gray-900 mb-0.5">{getSpecialty()}</p>
                        <p className="text-sm text-gray-500 font-medium italic">Primary query: {topCondition}</p>
                    </div>

                    {/* Clinical Markers */}
                    <div>
                        <div className="flex items-center gap-2 mb-3.5">
                            <span className="w-1.5 h-1.5 bg-primary-500 rounded-full"></span>
                            <span className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.1em]">Differential Summary</span>
                        </div>
                        <div className="space-y-2.5">
                            {conditions.slice(0, 3).map((c, i) => (
                                <div key={i} className="flex items-center justify-between p-3.5 rounded-xl border border-gray-50 bg-gray-50/30 hover:bg-white hover:shadow-sm transition-all">
                                    <div className="flex items-center gap-3">
                                        <div className="w-5 h-5 rounded-md bg-white border border-gray-100 flex items-center justify-center text-[10px] font-bold text-gray-400">
                                            0{i + 1}
                                        </div>
                                        <span className="text-[13.5px] font-semibold text-gray-800">{c.condition}</span>
                                    </div>
                                    <span className="text-[11px] font-bold text-primary-600 bg-primary-50 px-2.5 py-1 rounded-lg">
                                        {c.probability}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Clinical Recommendations (The "Yellow Box" Fix) */}
                    {rawSuggestions.length > 0 && (
                        <div>
                            <div className="flex items-center gap-2 mb-3.5">
                                <span className="w-1.5 h-1.5 bg-amber-500 rounded-full"></span>
                                <span className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.1em]">Clinical Next Steps</span>
                            </div>
                            <div className="bg-amber-50/50 border border-amber-100 rounded-2xl overflow-hidden">
                                <div className="p-4 space-y-4">
                                    {clinicalTests.length > 0 && (
                                        <div className="space-y-2">
                                            <p className="text-[11px] font-bold text-amber-700 flex items-center gap-1.5 uppercase">
                                                <FileSearch size={12} /> Suggested Diagnostics
                                            </p>
                                            <ul className="space-y-1.5">
                                                {clinicalTests.map((item, i) => (
                                                    <li key={i} className="text-[12.5px] text-amber-900/80 flex gap-2 leading-snug">
                                                        <ChevronRight size={14} className="shrink-0 mt-0.5 text-amber-400" />
                                                        {item}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                    {clarifications.length > 0 && (
                                        <div className="space-y-2 border-t border-amber-100/50 pt-3">
                                            <p className="text-[11px] font-bold text-amber-700 flex items-center gap-1.5 uppercase">
                                                <ClipboardList size={12} /> Clinical Context
                                            </p>
                                            <ul className="space-y-1.5">
                                                {clarifications.map((item, i) => (
                                                    <li key={i} className="text-[12.5px] text-amber-900/80 flex gap-2 leading-snug">
                                                        <ChevronRight size={14} className="shrink-0 mt-0.5 text-amber-400" />
                                                        {item}
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}

                </div>

                {/* Action Section */}
                <div className="p-7 pt-2 bg-gray-50/50 border-t border-gray-100">
                    <div className="grid grid-cols-2 gap-3.5 mb-5">
                        <a
                            href="tel:+911800"
                            className="flex flex-col items-center gap-1.5 bg-primary-600 hover:bg-primary-700 text-white py-3.5 rounded-[20px] transition-all shadow-md shadow-primary-200 active:scale-95"
                        >
                            <Phone size={18} />
                            <span className="text-[13px] font-bold">Call Doctor</span>
                        </a>
                        <a
                            href="https://www.practo.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex flex-col items-center gap-1.5 bg-white border border-gray-200 text-gray-800 hover:border-primary-300 hover:text-primary-700 py-3.5 rounded-[20px] transition-all active:scale-95 shadow-sm"
                        >
                            <MapPin size={18} />
                            <span className="text-[13px] font-bold">Find Nearby</span>
                        </a>
                    </div>

                    <div className="flex items-start gap-3 p-3.5 bg-white border border-gray-100 rounded-2xl shadow-sm italic">
                        <Clock size={15} className={`shrink-0 mt-0.5 ${isUrgent ? 'text-red-500' : 'text-primary-500'}`} />
                        <p className="text-[12px] text-gray-500 leading-relaxed font-medium">
                            {isUrgent
                                ? 'Consultation advised within 24 hours. Seek ER care if chest pain or breathlessness increases.'
                                : 'Routine evaluation advised. Present this brief to your physician during your next visit.'
                            }
                        </p>
                    </div>
                </div>
            </div>
        </div>
    )
}