module.exports = {
    content: ["./src/**/*.{js,jsx,ts,tsx}"],
    theme: {
        extend: {
            colors: {
                background: "#212121",
                surface: "#171717",
                "surface-light": "#2f2f2f",
                "surface-hover": "#3a3a3a",
                border: "#424242",
                // Chat UI primary accent
                accent: {
                    green: "#10a37f",
                    red: "#ef4444",
                    // Keep for non-chat pages (Landing, PendingAccess, etc.)
                    purple: "#7b2cbf",
                    blue: "#3a0ca3",
                },
                "t-primary": "#ececec",
                "t-secondary": "#b4b4b4",
                "t-tertiary": "#676767",
                // Keep primary ramp for non-chat pages (FineTune, ApiKeys, MedicalIntakeFlow, etc.)
                primary: {
                    50: "#f0f9ff",
                    100: "#e0f2fe",
                    200: "#bae6fd",
                    300: "#7dd3fc",
                    400: "#38bdf8",
                    500: "#0ea5e9",
                    600: "#0284c7",
                    700: "#0369a1",
                    800: "#075985",
                    900: "#0c4a6e",
                    950: "#082f49",
                },
            },
            fontFamily: {
                sans: ["Inter", "sans-serif"]
            },
            boxShadow: {
                'neon': '0 0 20px rgba(118, 44, 191, 0.5), 0 0 40px rgba(118, 44, 191, 0.3)',
            }
        }
    },
    plugins: [],
}
