import { useState } from 'react'
import { Star, CheckCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * FeedbackBar -- Phase 2 Feedback Collection Component
 * Shown below the AnalysisCard after council results are displayed.
 * Collects 1-5 star rating, optional doctor verification, and a correction.
 */
export default function FeedbackBar({ sessionId, patientId, topDiagnosis }) {
    const [rating, setRating] = useState(0)
    const [hovered, setHovered] = useState(0)
    const [submitted, setSubmitted] = useState(false)
    const [submitting, setSubmitting] = useState(false)
    const [expanded, setExpanded] = useState(false)
    const [doctorVerified, setDoctorVerified] = useState(false)
    const [correction, setCorrection] = useState('')
    const [notes, setNotes] = useState('')
    const [error, setError] = useState(null)

    const handleSubmit = async () => {
        if (!rating) return
        setSubmitting(true)
        setError(null)
        try {
            const res = await fetch(`${API_BASE}/feedback/council`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    patient_id: patientId || null,
                    rating: rating,
                    actual_diagnosis: correction.trim() || null,
                    doctor_verified: doctorVerified,
                    feedback_notes: notes.trim() || null,
                }),
            })
            const json = await res.json()
            if (json.success) {
                setSubmitted(true)
            } else {
                setError('Could not save feedback. Please try again.')
            }
        } catch (e) {
            setError('Network error. Please try again.')
        } finally {
            setSubmitting(false)
        }
    }

    if (submitted) {
        return (
            <div className="flex items-center gap-2 text-sm text-accent-green mt-4">
                <CheckCircle size={16} className="flex-shrink-0" />
                <span className="font-medium">Thank you for your feedback!</span>
                {doctorVerified && (
                    <span className="ml-auto text-xs text-accent-green/70">
                        Case saved to medical library
                    </span>
                )}
            </div>
        )
    }

    return (
        <div className="mt-4 border-t border-[#2f2f2f] pt-4 max-w-2xl mx-auto">
            {/* Main row */}
            <div className="flex items-center gap-3">
                <span className="text-xs text-[#676767] font-medium whitespace-nowrap">Was this helpful?</span>

                {/* Star rating */}
                <div className="flex gap-0.5">
                    {[1, 2, 3, 4, 5].map(star => (
                        <button
                            key={star}
                            id={`feedback-star-${star}`}
                            onMouseEnter={() => setHovered(star)}
                            onMouseLeave={() => setHovered(0)}
                            onClick={() => { setRating(star); if (star >= 4) setExpanded(true) }}
                            className="transition-all duration-150"
                            title={`${star} star${star > 1 ? 's' : ''}`}
                        >
                            <Star
                                size={16}
                                className={`transition-colors ${(hovered || rating) >= star
                                        ? 'fill-yellow-400 text-yellow-400'
                                        : 'text-[#424242]'
                                    }`}
                            />
                        </button>
                    ))}
                </div>

                {rating > 0 && !expanded && (
                    <span className="text-xs text-[#676767] italic">
                        {rating <= 2 ? 'Sorry to hear that.' : rating === 3 ? 'Thank you.' : 'Great!'}
                    </span>
                )}

                {/* Expand/collapse */}
                <button
                    onClick={() => setExpanded(p => !p)}
                    className="ml-auto text-[#676767] hover:text-[#b4b4b4] transition-colors"
                    title={expanded ? 'Collapse' : 'Add details'}
                >
                    {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {/* Quick submit */}
                {!expanded && rating > 0 && (
                    <button
                        id="feedback-submit"
                        onClick={handleSubmit}
                        disabled={submitting}
                        className="text-xs bg-accent-green hover:bg-[#0d8c6b] text-white px-3 py-1.5 rounded-lg font-medium transition-colors disabled:opacity-50 ml-1"
                    >
                        {submitting ? 'Saving...' : 'Submit'}
                    </button>
                )}
            </div>

            {/* Expanded detail form */}
            {expanded && (
                <div className="mt-3 pt-3 border-t border-[#2f2f2f] space-y-3">

                    {/* Doctor verification toggle */}
                    <label className="flex items-center gap-2 cursor-pointer group w-fit">
                        <div
                            onClick={() => setDoctorVerified(p => !p)}
                            className={`w-9 h-5 rounded-full transition-colors ${doctorVerified ? 'bg-accent-green' : 'bg-[#424242]'} relative flex-shrink-0`}
                        >
                            <div className={`absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform ${doctorVerified ? 'translate-x-4' : 'translate-x-0.5'}`} />
                        </div>
                        <span className="text-xs text-[#b4b4b4] group-hover:text-white transition-colors font-medium">
                            Doctor-verified diagnosis
                        </span>
                        {doctorVerified && (
                            <span className="text-xs text-accent-green">Saved to training library</span>
                        )}
                    </label>

                    {/* Actual diagnosis correction */}
                    <div>
                        <label className="text-xs text-[#676767] mb-1 block font-medium">
                            Correct diagnosis <span className="text-[#424242]">(optional)</span>
                        </label>
                        <input
                            id="feedback-correction"
                            type="text"
                            value={correction}
                            onChange={e => setCorrection(e.target.value)}
                            placeholder={`AI said: "${topDiagnosis || 'Unknown'}"`}
                            className="w-full bg-[#2f2f2f] border border-[#424242] rounded-lg px-3 py-2 text-sm text-white placeholder-[#676767] focus:outline-none focus:border-accent-green transition-colors"
                        />
                    </div>

                    {/* Additional notes */}
                    <div>
                        <label className="text-xs text-[#676767] mb-1 block font-medium">
                            Notes <span className="text-[#424242]">(optional)</span>
                        </label>
                        <textarea
                            id="feedback-notes"
                            value={notes}
                            onChange={e => setNotes(e.target.value)}
                            placeholder="What was correct or incorrect about this assessment?"
                            rows={2}
                            className="w-full bg-[#2f2f2f] border border-[#424242] rounded-lg px-3 py-2 text-sm text-white placeholder-[#676767] resize-none focus:outline-none focus:border-accent-green transition-colors"
                        />
                    </div>

                    {error && (
                        <div className="flex items-center gap-2 text-xs text-red-400">
                            <AlertCircle size={13} /> {error}
                        </div>
                    )}

                    <div className="flex items-center gap-2 pt-1">
                        <button
                            id="feedback-submit-expanded"
                            onClick={handleSubmit}
                            disabled={submitting || !rating}
                            className="bg-accent-green hover:bg-[#0d8c6b] text-white text-xs font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            {submitting ? 'Saving...' : 'Submit Feedback'}
                        </button>
                        <button
                            onClick={() => setExpanded(false)}
                            className="text-xs text-[#676767] hover:text-[#b4b4b4] transition-colors"
                        >
                            Cancel
                        </button>
                        {rating === 0 && (
                            <span className="text-xs text-[#676767] italic">Select a rating first</span>
                        )}
                    </div>
                </div>
            )}
        </div>
    )
}
