// Documentation Presentation Script
class DocumentationPresenter {
    constructor() {
        this.currentFile = 'README.md';
        this.markdownFiles = {
            'README.md': '/README.md',
            'CONFIGURATION.md': '/docs/CONFIGURATION.md',
            'DEVELOPER_HINTS.md': '/docs/DEVELOPER_HINTS.md',
            'ARCHITECTURE.md': '/docs/ARCHITECTURE.md',
            'REQUEST_RESPONSE_FLOW.md': '/docs/REQUEST_RESPONSE_FLOW.md',
            'API.md': '/docs/API.md',
            'TESTING.md': '/docs/TESTING.md',
            'CHART_BEHAVIOR.md': '/docs/CHART_BEHAVIOR.md',
            'PROMPT_MATRIX.md': '/docs/PROMPT_MATRIX.md'
        };
        
        // Search functionality
        this.searchIndex = [];
        this.searchTimeout = null;
        
        this.init();
    }

    init() {
        // Check if required libraries are loaded
        this.checkLibraries();
        
        this.setupEventListeners();
        this.loadMarkdownFile(this.currentFile);
        this.setupMarkedOptions();
        
        // Build search index in background (non-blocking)
        setTimeout(() => {
            this.buildSearchIndex().catch(error => {
                console.error('Search index building failed:', error);
            });
        }, 1000);
    }

    checkLibraries() {
        if (typeof marked === 'undefined') {
            console.warn('⚠️ Marked library not loaded - using fallback parser');
        } else {
            console.log('✅ Marked library loaded successfully');
        }
        
        if (typeof hljs === 'undefined') {
            console.warn('⚠️ Highlight.js library not loaded - code highlighting disabled');
        } else {
            console.log('✅ Highlight.js library loaded successfully');
        }
    }

    setupEventListeners() {
        // Navigation links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const file = e.target.closest('a').dataset.file;
                this.loadMarkdownFile(file);
                this.updateActiveNav(e.target.closest('a'));
            });
        });

        // Print button
        document.getElementById('print-btn').addEventListener('click', () => {
            window.print();
        });

        // Fullscreen button
        document.getElementById('fullscreen-btn').addEventListener('click', () => {
            this.toggleFullscreen();
        });

        // TOC toggle
        document.getElementById('toc-toggle').addEventListener('click', () => {
            this.toggleTOC();
        });

        // Mobile sidebar toggle
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeTOC();
                this.hideSearchResults();
            }
        });

        // Search functionality
        const searchInput = document.getElementById('search-input');
        const searchClear = document.getElementById('search-clear');

        searchInput.addEventListener('input', (e) => {
            this.handleSearchInput(e.target.value);
        });

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                this.performSearch(e.target.value);
            }
        });

        searchClear.addEventListener('click', () => {
            searchInput.value = '';
            this.hideSearchResults();
            searchInput.focus();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                searchInput.focus();
            }
        });

        // Smooth scrolling for anchor links
        document.addEventListener('click', (e) => {
            if (e.target.matches('a[href^="#"]')) {
                e.preventDefault();
                const target = document.querySelector(e.target.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    }

    setupMarkedOptions() {
        if (typeof marked === 'undefined') {
            console.warn('Marked library not loaded - markdown parsing disabled');
            return;
        }
        
        marked.setOptions({
            highlight: function(code, lang) {
                if (typeof hljs !== 'undefined' && lang && hljs.getLanguage(lang)) {
                    try {
                        return hljs.highlight(code, { language: lang }).value;
                    } catch (err) {
                        console.error('Highlight.js error:', err);
                    }
                }
                if (typeof hljs !== 'undefined') {
                    return hljs.highlightAuto(code).value;
                }
                return code; // Return unhighlighted code if hljs not available
            },
            breaks: true,
            gfm: true
        });
    }

    async loadMarkdownFile(filename) {
        const contentDiv = document.getElementById('content');
        const filePath = this.markdownFiles[filename];
        
        if (!filePath) {
            this.showError('File not found');
            return;
        }

        // Debug: Log the file path being requested
        console.log(`Loading file: ${filename} -> ${filePath}`);
        console.log(`Current URL: ${window.location.href}`);
        console.log(`Base URL: ${window.location.origin}`);

        // Show loading state
        contentDiv.innerHTML = `
            <div class="loading">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading ${filename}...</p>
            </div>
        `;

        try {
            // Construct full URL for debugging
            const fullUrl = new URL(filePath, window.location.origin).href;
            console.log(`Full URL being fetched: ${fullUrl}`);
            
            const response = await fetch(filePath);
            console.log(`Response status for ${filePath}: ${response.status}`);
            console.log(`Response headers:`, Object.fromEntries(response.headers.entries()));
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status} - ${response.statusText}`);
            }
            
            const markdown = await response.text();
            console.log(`Successfully loaded ${filename}, content length: ${markdown.length} characters`);
            
            let html;
            if (typeof marked !== 'undefined') {
                html = marked.parse(markdown);
            } else {
                // Fallback: simple markdown to HTML conversion
                html = this.simpleMarkdownToHtml(markdown);
            }
            
            contentDiv.innerHTML = `
                <div class="fade-in">
                    ${html}
                </div>
            `;

            // Update page title and breadcrumb
            this.updatePageInfo(filename);
            
            // Generate table of contents
            this.generateTOC();
            
            // Highlight code blocks (if highlight.js is available)
            if (typeof hljs !== 'undefined') {
                hljs.highlightAll();
            } else {
                console.warn('Highlight.js not loaded - code highlighting disabled');
            }
            
            // Add smooth scrolling to headings
            this.addHeadingAnchors();
            
        } catch (error) {
            console.error('Error loading markdown file:', error);
            console.error('Error details:', {
                filename,
                filePath,
                currentUrl: window.location.href,
                userAgent: navigator.userAgent
            });
            this.showError(`Failed to load ${filename}: ${error.message}`);
        }
    }

    showError(message) {
        const contentDiv = document.getElementById('content');
        contentDiv.innerHTML = `
            <div class="error-message">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Error</h3>
                <p>${message}</p>
                <button onclick="location.reload()" class="btn btn-secondary">
                    <i class="fas fa-redo"></i> Reload Page
                </button>
            </div>
        `;
    }

    // Simple fallback markdown parser when marked library is not available
    simpleMarkdownToHtml(markdown) {
        return markdown
            // Headers
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // Bold
            .replace(/\*\*(.*)\*\*/gim, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.*)\*/gim, '<em>$1</em>')
            // Code blocks
            .replace(/```([\s\S]*?)```/gim, '<pre><code>$1</code></pre>')
            // Inline code
            .replace(/`(.*?)`/gim, '<code>$1</code>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2">$1</a>')
            // Line breaks
            .replace(/\n/gim, '<br>');
    }

    updateActiveNav(activeLink) {
        // Remove active class from all links
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        
        // Add active class to clicked link
        activeLink.classList.add('active');
    }

    updatePageInfo(filename) {
        const pageNames = {
            'README.md': 'Project Overview',
            'CONFIGURATION.md': 'Configuration Guide',
            'DEVELOPER_HINTS.md': 'Developer Hints',
            'ARCHITECTURE.md': 'System Architecture',
            'REQUEST_RESPONSE_FLOW.md': 'Request-Response Flow',
            'API.md': 'API Reference',
            'TESTING.md': 'Testing Guide',
            'CHART_BEHAVIOR.md': 'Chart Behavior',
            'PROMPT_MATRIX.md': 'Prompt Engineering'
        };

        document.getElementById('current-page').textContent = pageNames[filename] || filename;
        document.title = `${pageNames[filename]} - DB Report Chat App Documentation`;
    }

    generateTOC() {
        const content = document.getElementById('content');
        const headings = content.querySelectorAll('h1, h2, h3, h4, h5, h6');
        const tocContent = document.getElementById('toc-content');
        
        if (headings.length === 0) {
            tocContent.innerHTML = '<p>No headings found</p>';
            return;
        }

        const toc = document.createElement('ul');
        
        headings.forEach((heading, index) => {
            const level = parseInt(heading.tagName.charAt(1));
            const text = heading.textContent;
            const id = `heading-${index}`;
            
            heading.id = id;
            
            const li = document.createElement('li');
            const a = document.createElement('a');
            
            a.href = `#${id}`;
            a.textContent = text;
            a.style.paddingLeft = `${(level - 1) * 15}px`;
            
            a.addEventListener('click', (e) => {
                e.preventDefault();
                heading.scrollIntoView({ behavior: 'smooth' });
                this.updateTOCActive(a);
            });
            
            li.appendChild(a);
            toc.appendChild(li);
        });
        
        tocContent.innerHTML = '';
        tocContent.appendChild(toc);
    }

    updateTOCActive(activeLink) {
        document.querySelectorAll('#toc-content a').forEach(link => {
            link.classList.remove('active');
        });
        activeLink.classList.add('active');
    }

    addHeadingAnchors() {
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        
        headings.forEach(heading => {
            if (!heading.id) {
                heading.id = 'heading-' + Math.random().toString(36).substr(2, 9);
            }
            
            const anchor = document.createElement('a');
            anchor.href = `#${heading.id}`;
            anchor.className = 'heading-anchor';
            anchor.innerHTML = '<i class="fas fa-link"></i>';
            anchor.style.display = 'none';
            
            heading.style.position = 'relative';
            heading.appendChild(anchor);
            
            heading.addEventListener('mouseenter', () => {
                anchor.style.display = 'inline-block';
            });
            
            heading.addEventListener('mouseleave', () => {
                anchor.style.display = 'none';
            });
        });
    }

    toggleTOC() {
        const tocSidebar = document.getElementById('toc-sidebar');
        tocSidebar.classList.toggle('active');
    }

    closeTOC() {
        const tocSidebar = document.getElementById('toc-sidebar');
        tocSidebar.classList.remove('active');
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen().catch(err => {
                console.error('Error attempting to enable fullscreen:', err);
            });
        } else {
            document.exitFullscreen();
        }
    }

    // Search functionality
    async buildSearchIndex() {
        console.log('Building search index...');
        this.searchIndex = [];
        
        // First, test if server is accessible
        try {
            const testResponse = await fetch('/README.md');
            if (!testResponse.ok) {
                console.warn('Server test failed - README.md not accessible');
                console.warn('This might indicate the server is not running or running from wrong directory');
                return;
            }
            console.log('✅ Server accessibility test passed');
        } catch (error) {
            console.warn('❌ Server accessibility test failed:', error.message);
            console.warn('Search index building will be skipped');
            return;
        }
        
        const pageNames = {
            'README.md': 'Project Overview',
            'CONFIGURATION.md': 'Configuration Guide',
            'DEVELOPER_HINTS.md': 'Developer Hints',
            'ARCHITECTURE.md': 'System Architecture',
            'REQUEST_RESPONSE_FLOW.md': 'Request-Response Flow',
            'API.md': 'API Reference',
            'TESTING.md': 'Testing Guide',
            'CHART_BEHAVIOR.md': 'Chart Behavior',
            'PROMPT_MATRIX.md': 'Prompt Engineering'
        };
        
        for (const [filename, filepath] of Object.entries(this.markdownFiles)) {
            try {
                console.log(`Indexing ${filename} from ${filepath}...`);
                const response = await fetch(filepath);
                
                if (response.ok) {
                    const content = await response.text();
                    console.log(`Successfully indexed ${filename} (${content.length} characters)`);
                    
                    this.searchIndex.push({
                        filename,
                        title: pageNames[filename] || filename,
                        content: content.toLowerCase(),
                        filepath
                    });
                } else {
                    console.warn(`Failed to index ${filename}: HTTP ${response.status} - ${response.statusText}`);
                }
            } catch (error) {
                console.warn(`Failed to index ${filename}:`, error.message);
                console.warn(`File path: ${filepath}`);
                console.warn(`Current URL: ${window.location.href}`);
            }
        }
        
        console.log(`Search index built with ${this.searchIndex.length} documents`);
        
        // If no documents were indexed, show a warning
        if (this.searchIndex.length === 0) {
            console.error('⚠️ No documents were indexed! This might indicate:');
            console.error('1. Server is not running');
            console.error('2. Server is running from wrong directory');
            console.error('3. Network connectivity issues');
            console.error('4. CORS issues');
        }
    }

    handleSearchInput(query) {
        const searchClear = document.getElementById('search-clear');
        const searchIcon = document.querySelector('.search-icon');
        
        if (query.trim()) {
            searchClear.style.display = 'block';
            
            // Show loading state
            searchIcon.className = 'fas fa-spinner fa-spin search-icon';
            
            // Debounce search
            if (this.searchTimeout) {
                clearTimeout(this.searchTimeout);
            }
            
            this.searchTimeout = setTimeout(() => {
                this.performSearch(query);
                // Restore search icon
                searchIcon.className = 'fas fa-search search-icon';
            }, 300);
        } else {
            searchClear.style.display = 'none';
            searchIcon.className = 'fas fa-search search-icon';
            this.hideSearchResults();
        }
    }

    performSearch(query) {
        if (!query.trim()) {
            this.hideSearchResults();
            return;
        }

        const results = this.searchInIndex(query.toLowerCase());
        this.displaySearchResults(results, query);
    }

    searchInIndex(query) {
        const results = [];
        
        for (const doc of this.searchIndex) {
            const matches = [];
            const lines = doc.content.split('\n');
            
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];
                if (line.includes(query)) {
                    const excerpt = this.createExcerpt(line, query, 100);
                    matches.push({
                        line: i + 1,
                        excerpt,
                        score: this.calculateScore(line, query)
                    });
                }
            }
            
            if (matches.length > 0) {
                results.push({
                    filename: doc.filename,
                    title: doc.title,
                    filepath: doc.filepath,
                    matches: matches.sort((a, b) => b.score - a.score).slice(0, 3)
                });
            }
        }
        
        return results.sort((a, b) => {
            const aScore = Math.max(...a.matches.map(m => m.score));
            const bScore = Math.max(...b.matches.map(m => m.score));
            return bScore - aScore;
        });
    }

    calculateScore(line, query) {
        let score = 0;
        
        // Exact match gets highest score
        if (line.includes(query)) {
            score += 10;
        }
        
        // Word boundary matches
        const words = query.split(' ').filter(w => w.length > 2);
        for (const word of words) {
            if (line.includes(word)) {
                score += 5;
            }
        }
        
        // Header matches get bonus
        if (line.startsWith('#')) {
            score += 3;
        }
        
        return score;
    }

    createExcerpt(text, query, maxLength) {
        const index = text.toLowerCase().indexOf(query.toLowerCase());
        if (index === -1) return text.substring(0, maxLength);
        
        const start = Math.max(0, index - 30);
        const end = Math.min(text.length, index + query.length + 30);
        let excerpt = text.substring(start, end);
        
        if (start > 0) excerpt = '...' + excerpt;
        if (end < text.length) excerpt = excerpt + '...';
        
        return excerpt;
    }

    displaySearchResults(results, query) {
        const resultsContainer = document.getElementById('search-results');
        
        if (results.length === 0) {
            resultsContainer.innerHTML = `
                <div class="search-results-header">
                    Search Results
                </div>
                <div class="search-no-results">
                    <i class="fas fa-search"></i>
                    <p>No results found for "<strong>${query}</strong>"</p>
                    <p style="font-size: 12px; margin-top: 8px;">Try different keywords or check spelling</p>
                </div>
            `;
        } else {
            let html = `
                <div class="search-results-header">
                    Found ${results.length} result${results.length > 1 ? 's' : ''} for "${query}"
                </div>
            `;
            
            for (const result of results.slice(0, 8)) { // Limit to 8 results for better UX
                const matchCount = result.matches.length;
                html += `
                    <div class="search-result-item" data-file="${result.filename}">
                        <div class="search-result-title">${result.title}</div>
                        <div class="search-result-file">${result.filename} • ${matchCount} match${matchCount > 1 ? 'es' : ''}</div>
                        <div class="search-result-excerpt">
                            ${this.highlightQuery(result.matches[0].excerpt, query)}
                        </div>
                    </div>
                `;
            }
            
            if (results.length > 8) {
                html += `
                    <div class="search-result-item" style="text-align: center; color: #667eea; font-style: italic;">
                        ... and ${results.length - 8} more results
                    </div>
                `;
            }
            
            resultsContainer.innerHTML = html;
            
            // Add click handlers
            resultsContainer.querySelectorAll('.search-result-item').forEach(item => {
                if (item.dataset.file) { // Only add handlers to actual results
                    item.addEventListener('click', () => {
                        const filename = item.dataset.file;
                        this.loadMarkdownFile(filename);
                        this.hideSearchResults();
                        document.getElementById('search-input').value = '';
                        document.getElementById('search-clear').style.display = 'none';
                    });
                }
            });
        }
        
        resultsContainer.style.display = 'block';
    }

    highlightQuery(text, query) {
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        return text.replace(regex, '<span class="search-highlight">$1</span>');
    }

    hideSearchResults() {
        const resultsContainer = document.getElementById('search-results');
        resultsContainer.style.display = 'none';
    }

    // Keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + K: Focus search
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                document.getElementById('search-input').focus();
            }
            
            // Ctrl/Cmd + /: Toggle TOC
            if ((e.ctrlKey || e.metaKey) && e.key === '/') {
                e.preventDefault();
                this.toggleTOC();
            }
        });
    }
}

// Initialize the documentation presenter when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.docPresenter = new DocumentationPresenter();
});

// Add some utility functions
window.DocUtils = {
    // Copy code block to clipboard
    copyCode: function(codeElement) {
        const text = codeElement.textContent;
        navigator.clipboard.writeText(text).then(() => {
            // Show success message
            const originalText = codeElement.textContent;
            codeElement.textContent = 'Copied!';
            setTimeout(() => {
                codeElement.textContent = originalText;
            }, 2000);
        });
    },

    // Toggle code block visibility
    toggleCode: function(button) {
        const codeBlock = button.nextElementSibling;
        codeBlock.style.display = codeBlock.style.display === 'none' ? 'block' : 'none';
        button.textContent = codeBlock.style.display === 'none' ? 'Show Code' : 'Hide Code';
    },

    // Search functionality
    search: function(query) {
        const content = document.getElementById('content');
        const text = content.textContent.toLowerCase();
        const searchTerm = query.toLowerCase();
        
        if (text.includes(searchTerm)) {
            // Highlight search results
            const regex = new RegExp(`(${searchTerm})`, 'gi');
            content.innerHTML = content.innerHTML.replace(regex, '<mark>$1</mark>');
        }
    }
};

// Add copy buttons to code blocks
document.addEventListener('DOMContentLoaded', () => {
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach(block => {
        const copyButton = document.createElement('button');
        copyButton.className = 'copy-btn';
        copyButton.innerHTML = '<i class="fas fa-copy"></i>';
        copyButton.onclick = () => window.DocUtils.copyCode(block);
        
        block.parentElement.style.position = 'relative';
        block.parentElement.appendChild(copyButton);
    });
}); 