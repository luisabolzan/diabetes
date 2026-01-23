# Diabetes Manager - iOS PWA

This project is a Progressive Web App (PWA) designed for Diabetes Management, optimized for iOS (Safari).

## Purpose
This application functions as a standalone mobile app on iOS devices without requiring the App Store. It is built using modern web technologies (Vite + React) and configured for offline usage and "Add to Home Screen" capability.

## Folder Structure
- **public/**: Static assets.
  - `manifest.json`: Configuration for iOS home screen behavior (icons, name, display mode).
  - `service-worker.js`: Handles offline caching of the application bundle.
  - `icons/`: App icons for various iOS sizes.
- **src/**: Application source code.
  - `main.jsx`: Entry point.
  - `styles/`: Custom CSS using the "Deep Ocean" theme.
- **vite.config.js**: Build configuration ensuring relative paths for static hosting.

## Limitations & Constraints
- **Platform**: Optimized for iOS Safari.
- **Native APIs**: Does NOT use native device features (Camera, Bluetooth, etc.) to ensure compatibility and privacy.
- **Distribution**: Intended for personal use via "Add to Home Screen", not the App Store.

## Development

Prerequisites: Node.js installed.

1. **Install Dependencies**
   ```bash
   npm install
   ```

2. **Run Locally**
   ```bash
   npm run dev
   ```
   Access at `http://localhost:5173` (or similar).

## Build Instructions

To create the production bundle:

```bash
npm run build
```

The output will be in the `dist/` folder. This folder can be uploaded to any static host (GitHub Pages, Vercel, Netlify).

## Installation on iOS

1. Deploy the `dist/` folder to a secure HTTPS URL (e.g., Vercel or GitHub Pages).
2. Open the URL in **Safari** on your iPhone/iPad.
3. Tap the **Share** button (box with arrow pointing up).
4. Scroll down and tap **"Add to Home Screen"**.
5. Confirm the name and tap **Add**.

The app will now appear on your home screen and run in standalone mode like a native app.
