Create a new repository for an iOS mobile version of the project implemented as a Progressive Web App (PWA) using Vite + React.

Initialize the repository with the following structure and requirements:

Repository Structure
mobile-ios-pwa/
├─ index.html
├─ package.json
├─ vite.config.js
├─ public/
│  ├─ manifest.json
│  ├─ service-worker.js
│  └─ icons/
│     ├─ icon-180x180.png
│     ├─ icon-192x192.png
│     └─ icon-512x512.png
├─ src/
│  ├─ main.jsx
│  ├─ App.jsx
│  ├─ components/
│  └─ styles/
└─ README.md

Technical Requirements

Use Vite + React as the build system.

Configure the project to be deployable as a static site.

Ensure compatibility with Safari on iOS.

Implement basic offline support using a service worker compatible with iOS.

Configure manifest.json for Add to Home Screen behavior on iOS.

Do not use the camera or advanced native APIs.

No App Store, Xcode, Mac, or Apple Developer account should be required.

Intended for personal use only.

README

Populate README.md with:

A description of the iOS PWA purpose

Folder structure explanation

Constraints and limitations (iOS Safari, no native APIs)

Development instructions using Vite (npm install, npm run dev)

Build instructions (npm run build, npm run preview)

Steps to install the PWA on iOS via Safari → Add to Home Screen

Add clear comments in configuration files explaining key PWA and iOS compatibility decisions.