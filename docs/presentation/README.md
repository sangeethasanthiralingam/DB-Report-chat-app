# Documentation Presentation - DB Report Chat App

## 🚀 Quick Start

### Windows
```bash
# Double-click the launcher
launch.bat

# Or run manually
cd "D:\project\first try\DB Report chat app"
python -m http.server 8000
# Then visit: http://localhost:8000/docs/presentation/
```

### macOS/Linux
```bash
# Make executable and run
chmod +x launch.sh
./launch.sh

# Or run manually
cd "/path/to/DB Report chat app"
python3 -m http.server 8000
# Then visit: http://localhost:8000/docs/presentation/
```

## 📁 File Structure

```
docs/presentation/
├── index.html              # Main presentation page
├── styles.css              # Presentation styles
├── script.js               # Presentation logic
├── launch.bat              # Windows launcher
├── launch.sh               # Unix launcher
├── server_test.py          # Server test script
├── test_server.html        # Debug/test page
├── search-demo.html        # Search functionality demo
└── README.md               # This file
```

## 🎯 Features

- **Sidebar Navigation**: Easy navigation between documents
- **Breadcrumb Navigation**: Shows current location
- **Table of Contents**: Auto-generated from markdown headers
- **Search Functionality**: Real-time search across all documents
- **Responsive Design**: Works on desktop and mobile
- **Print Support**: Optimized for printing
- **Fullscreen Mode**: Distraction-free reading
- **Code Highlighting**: Syntax highlighting for code blocks
- **Copy Code**: One-click code copying
- **Smooth Scrolling**: Smooth navigation between sections

## 📚 Documentation Order

The presentation follows this logical order:

1. **README.md** - Project overview and quick start
2. **CONFIGURATION.md** - Environment setup
3. **DEVELOPER_HINTS.md** - Development guide
4. **ARCHITECTURE.md** - System architecture
5. **REQUEST_RESPONSE_FLOW.md** - Detailed flow diagrams
6. **API.md** - API reference
7. **TESTING.md** - Testing procedures
8. **CHART_BEHAVIOR.md** - Chart generation details
9. **PROMPT_MATRIX.md** - Prompt engineering

## 🔍 Search Features

- **Real-time Search**: Results update as you type
- **Debounced Input**: Prevents excessive API calls
- **Search Highlights**: Matched terms are highlighted
- **Search Excerpts**: Context around matches is shown
- **Keyboard Shortcuts**: 
  - `Ctrl+F` / `Cmd+F`: Focus search box
  - `Escape`: Clear search
  - `Enter`: Navigate to first result

## 🎨 Customization

### Styling
Edit `styles.css` to customize:
- Colors and themes
- Fonts and typography
- Layout and spacing
- Responsive breakpoints

### Content
Edit `script.js` to:
- Add new documents
- Change navigation order
- Modify search behavior
- Add custom features

### Configuration
Key settings in `script.js`:
```javascript
// Document order
this.documentOrder = ['README.md', 'CONFIGURATION.md', ...];

// Search settings
this.searchDebounceMs = 300;
this.maxSearchResults = 10;

// Chart settings
this.useInteractiveCharts = false;
```

## 🔧 Technical Details

### Dependencies
- **Marked.js**: Markdown parsing
- **Highlight.js**: Code syntax highlighting
- **Font Awesome**: Icons
- **Chart.js**: Interactive charts (optional)

### Browser Support
- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

### Performance
- Lazy loading of markdown files
- Debounced search input
- Efficient DOM manipulation
- Minimal external dependencies

## 🚀 Deployment

### Local Development
```bash
# Start server from project root
python -m http.server 8000
```

### Production
```bash
# Use a production server like nginx
# Copy docs/presentation/ to your web server
# Configure proper MIME types for .md files
```

### Docker
```dockerfile
# Example Dockerfile
FROM nginx:alpine
COPY docs/presentation/ /usr/share/nginx/html/
COPY docs/ /usr/share/nginx/html/docs/
```

## 🐛 Debugging

### Enable Debug Mode
```javascript
// In browser console
localStorage.setItem('debug', 'true');
location.reload();
```

### Check Console
Open browser developer tools to see:
- File loading errors
- JavaScript errors
- Network requests
- Search functionality logs

### Test Individual Files
```bash
# Test direct file access
curl http://localhost:8000/docs/ARCHITECTURE.md
curl http://localhost:8000/README.md
```

## 📞 Support

If you encounter issues:

1. **Check the debug page**: `http://localhost:8000/docs/presentation/test_server.html`
2. **Run the test script**: `python docs/presentation/server_test.py`
3. **Check browser console**: For JavaScript errors
4. **Verify file paths**: Ensure markdown files exist
5. **Test server directory**: Confirm server runs from project root

---

**Note**: This presentation requires a local HTTP server. Opening `index.html` directly in a browser will not work due to CORS restrictions when loading markdown files. 