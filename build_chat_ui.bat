@echo off
echo 🚀 Building StillMe AI Chat UI for Production...

echo 📦 Installing dependencies...
call npm install

echo 🔨 Building for production...
call npm run build

echo ✅ Build completed!
echo 📁 Output directory: dist/
echo 🌐 You can serve the files from dist/ folder

echo.
echo 📋 To serve the built files:
echo 1. Install a static server: npm install -g serve
echo 2. Run: serve -s dist -l 3000
echo 3. Or upload dist/ folder to any web hosting

pause
