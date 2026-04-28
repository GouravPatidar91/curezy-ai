import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL
const supabaseKey = process.env.REACT_APP_SUPABASE_ANON_KEY

// Prevent multiple instances during Hot Module Replacement (HMR)
// which causes "Lock broken by another request with the 'steal' option"
let supabaseClient;
if (!window.supabaseInstance) {
    window.supabaseInstance = createClient(supabaseUrl, supabaseKey)
}
supabaseClient = window.supabaseInstance

export const supabase = supabaseClient
