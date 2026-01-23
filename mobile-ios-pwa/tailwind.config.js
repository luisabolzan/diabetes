/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                'deep-ocean': '#0f172a',
            },
            padding: {
                'safe': 'env(safe-area-inset-bottom)',
            }
        },
    },
    plugins: [],
}
