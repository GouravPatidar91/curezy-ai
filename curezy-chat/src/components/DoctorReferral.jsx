import { X, Phone, MapPin, Clock, AlertTriangle } from 'lucide-react'

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
        'default': 'General Physician',
    }

    const getSpecialty = () => {
        for (const [key, spec] of Object.entries(specialties)) {
            if (topCondition.toLowerCase().includes(key.toLowerCase())) return spec
        }
        return specialties.default
    }

    return (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-3xl shadow-2xl w-full max-w-md fade-in">

                {/* Header */}
                <div className={`p-6 rounded-t-3xl ${isUrgent ? 'bg-red-50' : 'bg-primary-50'}`}>
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                            {isUrgent && <AlertTriangle size={20} className="text-red-600" />}
                            <h2 className="font-bold text-gray-900">
                                {isUrgent ? 'Doctor Review Required' : 'See a Doctor'}
                            </h2>
                        </div>
                        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                            <X size={20} />
                        </button>
                    </div>
                    <p className="text-sm text-gray-600">
                        {isUrgent
                            ? 'Based on your assessment, we strongly recommend seeing a doctor soon.'
                            : 'For a professional diagnosis, we recommend consulting a doctor.'
                        }
                    </p>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">

                    {/* Recommended specialty */}
                    <div className="bg-gray-50 rounded-2xl p-4">
                        <p className="text-xs text-gray-500 font-medium mb-1">RECOMMENDED SPECIALIST</p>
                        <p className="text-lg font-bold text-primary-700">{getSpecialty()}</p>
                        <p className="text-sm text-gray-500">For: {topCondition}</p>
                    </div>

                    {/* What to tell doctor */}
                    <div>
                        <p className="text-xs text-gray-500 font-medium mb-2">WHAT TO TELL YOUR DOCTOR</p>
                        <div className="space-y-1">
                            {conditions.map((c, i) => (
                                <div key={i} className="flex items-center gap-2 text-sm text-gray-700">
                                    <div className="w-4 h-4 bg-primary-100 rounded-full flex items-center justify-center text-xs text-primary-700 font-bold flex-shrink-0">
                                        {i + 1}
                                    </div>
                                    {c.condition} ({c.probability}% likely)
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Missing data */}
                    {analysis?.missing_data_suggestions?.length > 0 && (
                        <div className="border border-yellow-200 bg-yellow-50 rounded-xl p-3">
                            <p className="text-xs font-semibold text-yellow-700 mb-1">Tests to Request</p>
                            {analysis.missing_data_suggestions.map((item, i) => (
                                <p key={i} className="text-xs text-yellow-700">• {item}</p>
                            ))}
                        </div>
                    )}

                    {/* Action buttons */}
                    <div className="grid grid-cols-2 gap-3 pt-2">
                        <a
                            href="tel:+911800"
                            className="flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 text-white py-3 rounded-xl text-sm font-medium transition-all"
                        >
                            <Phone size={16} />
                            Call Doctor
                        </a>
                        <a
                            href="https://www.practo.com"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex items-center justify-center gap-2 border border-primary-200 text-primary-700 hover:bg-primary-50 py-3 rounded-xl text-sm font-medium transition-all"
                        >
                            <MapPin size={16} />
                            Find Nearby
                        </a>
                    </div>

                    {/* Timing advice */}
                    <div className="flex items-center gap-2 text-xs text-gray-500 bg-gray-50 rounded-xl p-3">
                        <Clock size={14} className="flex-shrink-0" />
                        {isUrgent
                            ? 'Please visit a doctor within 24 hours or go to emergency if symptoms worsen.'
                            : 'Schedule an appointment within the next few days for a proper evaluation.'
                        }
                    </div>
                </div>
            </div>
        </div>
    )
}