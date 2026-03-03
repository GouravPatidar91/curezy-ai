module.exports = {
    content: ["./src/**/*.{js,jsx,ts,tsx}"],
    theme: {
        extend: {
            colors: {
                background: "#050505",
                surface: "#111111",
                "surface-light": "#1a1a1a",
                border: "#333333",
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
                accent: {
                    red: "#ff3333",
                    purple: "#7b2cbf",
                    blue: "#3a0ca3",
                }
            },
            fontFamily: {
                sans: ["Inter", "sans-serif"]
            },
            backgroundImage: {
                'radial-glow': 'radial-gradient(circle at center, var(--tw-gradient-stops))',
                'glass-gradient': 'linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
                'neon-gradient': 'linear-gradient(90deg, #ff3333 0%, #7b2cbf 50%, #3a0ca3 100%)',
            },
            boxShadow: {
                'neon': '0 0 20px rgba(118, 44, 191, 0.5), 0 0 40px rgba(118, 44, 191, 0.3)',
                'neon-blue': '0 0 20px rgba(14, 165, 233, 0.5), 0 0 40px rgba(14, 165, 233, 0.3)',
                'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.3)',
            }
        }
    },
    plugins: [],
}