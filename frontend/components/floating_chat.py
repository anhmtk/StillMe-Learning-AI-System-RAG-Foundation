"""
Floating Chat Widget Component for Streamlit
Creates a resizable, draggable, fullscreen-capable chat panel that overlays the dashboard.
Similar to Notepad overlay on desktop - can be resized, dragged, and fullscreened.
"""
import streamlit.components.v1 as components
import json

def render_floating_chat(chat_history: list, api_base: str, is_open: bool = False):
    """
    Render a floating chat widget using HTML/CSS/JS.
    
    Features:
    - Resizable (drag corners/edges)
    - Draggable (drag header)
    - Fullscreen mode
    - Overlay mode (covers dashboard)
    - Auto-scroll messages
    - Enter to send
    
    Args:
        chat_history: List of chat messages in format [{"role": "user|assistant", "content": "..."}]
        api_base: Base URL for the API
        is_open: Whether the chat panel should be open by default
    
    Returns:
        Component instance
    """
    
    # Prepare chat history for JavaScript
    chat_history_json = json.dumps(chat_history)
    
    # HTML/CSS/JS for floating chat widget
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            /* CRITICAL: Ensure body/html take full viewport */
            html, body {{
                margin: 0;
                padding: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
            }}
            
            /* Overlay backdrop - covers dashboard when chat is open */
            #stillme-chat-overlay {{
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                background: rgba(0, 0, 0, 0.3) !important;
                z-index: 999999 !important;
                display: {'block' if is_open else 'none'} !important;
                pointer-events: auto !important;
            }}
            
            #stillme-chat-widget {{
                position: fixed !important;
                z-index: 1000000 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                pointer-events: none !important;
            }}
            
            #stillme-chat-widget * {{
                pointer-events: auto !important;
            }}
            
            #stillme-chat-button {{
                position: fixed !important;
                bottom: 20px !important;
                right: 20px !important;
                width: 60px !important;
                height: 60px !important;
                border-radius: 50% !important;
                background: linear-gradient(135deg, #46b3ff 0%, #1e90ff 100%) !important;
                border: 3px solid #ffffff !important;
                color: white !important;
                font-size: 28px !important;
                cursor: pointer !important;
                box-shadow: 0 4px 20px rgba(70, 179, 255, 0.6), 0 0 0 4px rgba(70, 179, 255, 0.2) !important;
                transition: all 0.3s ease !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                z-index: 2147483647 !important; /* Maximum z-index value */
                visibility: visible !important;
                opacity: 1 !important;
                pointer-events: auto !important;
                margin: 0 !important;
                padding: 0 !important;
            }}
            
            #stillme-chat-button:hover {{
                transform: scale(1.15) !important;
                box-shadow: 0 6px 24px rgba(70, 179, 255, 0.8), 0 0 0 6px rgba(70, 179, 255, 0.3) !important;
            }}
            
            /* Ensure button is always visible - even if panel is open */
            #stillme-chat-button:not(:disabled) {{
                display: flex !important;
                visibility: visible !important;
                opacity: 1 !important;
            }}
            
            #stillme-chat-panel {{
                position: fixed !important;
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
                width: 600px !important;
                height: 700px !important;
                min-width: 400px !important;
                min-height: 400px !important;
                max-width: 95vw !important;
                max-height: 95vh !important;
                background: #0e1117 !important;
                border-radius: 12px !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8) !important;
                display: {'flex' if is_open else 'none'} !important;
                flex-direction: column !important;
                border: 1px solid #262730 !important;
                overflow: hidden !important;
                resize: both !important; /* Browser native resize (fallback) */
                z-index: 1000000 !important;
            }}
            
            /* Fullscreen mode */
            #stillme-chat-panel.fullscreen {{
                top: 0 !important;
                left: 0 !important;
                transform: none !important;
                width: 100vw !important;
                height: 100vh !important;
                max-width: 100vw !important;
                max-height: 100vh !important;
                border-radius: 0 !important;
                resize: none !important;
            }}
            
            /* Resize handles - 8 handles (4 corners + 4 edges) */
            .resize-handle {{
                position: absolute;
                background: transparent;
                z-index: 10;
            }}
            
            /* Corner handles */
            .resize-handle.nw {{ top: 0; left: 0; width: 10px; height: 10px; cursor: nw-resize; }}
            .resize-handle.ne {{ top: 0; right: 0; width: 10px; height: 10px; cursor: ne-resize; }}
            .resize-handle.sw {{ bottom: 0; left: 0; width: 10px; height: 10px; cursor: sw-resize; }}
            .resize-handle.se {{ bottom: 0; right: 0; width: 10px; height: 10px; cursor: se-resize; }}
            
            /* Edge handles */
            .resize-handle.n {{ top: 0; left: 10px; right: 10px; height: 10px; cursor: n-resize; }}
            .resize-handle.s {{ bottom: 0; left: 10px; right: 10px; height: 10px; cursor: s-resize; }}
            .resize-handle.e {{ top: 10px; bottom: 10px; right: 0; width: 10px; cursor: e-resize; }}
            .resize-handle.w {{ top: 10px; bottom: 10px; left: 0; width: 10px; cursor: w-resize; }}
            
            /* Visual resize indicator (optional - subtle) */
            .resize-handle:hover {{
                background: rgba(70, 179, 255, 0.2);
            }}
            
            .stillme-chat-header {{
                background: #262730;
                padding: 16px 20px;
                border-bottom: 1px solid #3a3d47;
                display: flex;
                justify-content: space-between;
                align-items: center;
                cursor: move; /* Indicate draggable */
                user-select: none; /* Prevent text selection when dragging */
            }}
            
            .stillme-chat-header h3 {{
                margin: 0;
                color: #46b3ff;
                font-size: 18px;
                font-weight: 600;
                flex: 1;
            }}
            
            .stillme-chat-header-buttons {{
                display: flex;
                gap: 8px;
                align-items: center;
            }}
            
            .stillme-chat-header-btn {{
                background: none;
                border: none;
                color: #ffffff;
                font-size: 18px;
                cursor: pointer;
                padding: 4px 8px;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                transition: background 0.2s;
            }}
            
            .stillme-chat-header-btn:hover {{
                background: #3a3d47;
            }}
            
            .stillme-chat-close {{
                background: none;
                border: none;
                color: #ffffff;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                transition: background 0.2s;
            }}
            
            .stillme-chat-close:hover {{
                background: #3a3d47;
            }}
            
            .stillme-chat-messages {{
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 12px;
            }}
            
            .stillme-chat-message {{
                padding: 12px 16px;
                border-radius: 8px;
                max-width: 80%;
                word-wrap: break-word;
            }}
            
            .stillme-chat-message.user {{
                background: #46b3ff;
                color: white;
                align-self: flex-end;
                margin-left: auto;
            }}
            
            .stillme-chat-message.assistant {{
                background: #262730;
                color: #ffffff;
                align-self: flex-start;
            }}
            
            .stillme-chat-input-container {{
                padding: 16px 20px;
                border-top: 1px solid #262730;
                background: #0e1117;
            }}
            
            .stillme-chat-input-wrapper {{
                display: flex;
                gap: 8px;
            }}
            
            #stillme-chat-input {{
                flex: 1;
                padding: 12px 16px;
                background: #262730;
                border: 1px solid #3a3d47;
                border-radius: 8px;
                color: #ffffff;
                font-size: 14px;
                font-family: inherit;
                resize: none;
            }}
            
            #stillme-chat-input:focus {{
                outline: none;
                border-color: #46b3ff;
            }}
            
            #stillme-chat-send {{
                padding: 12px 24px;
                background: #46b3ff;
                border: none;
                border-radius: 8px;
                color: white;
                font-weight: 600;
                cursor: pointer;
                transition: background 0.2s;
            }}
            
            #stillme-chat-send:hover {{
                background: #1e90ff;
            }}
            
            #stillme-chat-send:disabled {{
                background: #3a3d47;
                cursor: not-allowed;
            }}
            
            /* Scrollbar styling */
            .stillme-chat-messages::-webkit-scrollbar {{
                width: 6px;
            }}
            
            .stillme-chat-messages::-webkit-scrollbar-track {{
                background: #0e1117;
            }}
            
            .stillme-chat-messages::-webkit-scrollbar-thumb {{
                background: #262730;
                border-radius: 3px;
            }}
            
            .stillme-chat-messages::-webkit-scrollbar-thumb:hover {{
                background: #3a3d47;
            }}
        </style>
    </head>
    <body>
        <script>
            // Debug: Log when body loads
            console.log('StillMe Chat: HTML body loaded');
            console.log('StillMe Chat: Window dimensions:', window.innerWidth, 'x', window.innerHeight);
        </script>
        
        <!-- Overlay backdrop - covers dashboard when chat is open -->
        <div id="stillme-chat-overlay" onclick="toggleChat()"></div>
        
        <div id="stillme-chat-widget">
            <div id="stillme-chat-panel">
                <!-- Resize handles (8 handles: 4 corners + 4 edges) -->
                <div class="resize-handle nw"></div>
                <div class="resize-handle ne"></div>
                <div class="resize-handle sw"></div>
                <div class="resize-handle se"></div>
                <div class="resize-handle n"></div>
                <div class="resize-handle s"></div>
                <div class="resize-handle e"></div>
                <div class="resize-handle w"></div>
                
                <!-- Header (draggable) -->
                <div class="stillme-chat-header" id="stillme-chat-header">
                    <h3>💬 Chat with StillMe</h3>
                    <div class="stillme-chat-header-buttons">
                        <button class="stillme-chat-header-btn" id="fullscreen-btn" onclick="toggleFullscreen()" title="Toggle Fullscreen">⛶</button>
                        <button class="stillme-chat-close" onclick="toggleChat()" title="Close">×</button>
                    </div>
                </div>
                
                <!-- Messages container (auto-scroll) -->
                <div class="stillme-chat-messages" id="stillme-chat-messages">
                    <!-- Messages will be rendered here -->
                </div>
                
                <!-- Input container -->
                <div class="stillme-chat-input-container">
                    <div class="stillme-chat-input-wrapper">
                        <textarea 
                            id="stillme-chat-input" 
                            placeholder="Type your message... (Press Enter to send, Shift+Enter for new line)"
                            rows="2"
                        ></textarea>
                        <button id="stillme-chat-send" onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
            <button id="stillme-chat-button" onclick="toggleChat()">💬</button>
        </div>
        
        <script>
            const API_BASE = '{api_base}';
            let chatHistory = {chat_history_json};
            let isOpen = {str(is_open).lower()};
            
            // Panel state
            let isFullscreen = false;
            let isDragging = false;
            let isResizing = false;
            let resizeHandle = null;
            let dragStartX = 0;
            let dragStartY = 0;
            let panelStartX = 0;
            let panelStartY = 0;
            let panelStartWidth = 0;
            let panelStartHeight = 0;
            
            // Get panel element
            const panel = document.getElementById('stillme-chat-panel');
            const overlay = document.getElementById('stillme-chat-overlay');
            const header = document.getElementById('stillme-chat-header');
            
            // Load saved position/size from localStorage
            function loadPanelState() {{
                const saved = localStorage.getItem('stillme_chat_panel_state');
                if (saved) {{
                    try {{
                        const state = JSON.parse(saved);
                        if (state.width) panel.style.width = state.width;
                        if (state.height) panel.style.height = state.height;
                        if (state.left) panel.style.left = state.left;
                        if (state.top) panel.style.top = state.top;
                        if (state.transform) panel.style.transform = state.transform;
                    }} catch (e) {{
                        console.warn('Failed to load panel state:', e);
                    }}
                }}
            }}
            
            // Save panel state to localStorage
            function savePanelState() {{
                const state = {{
                    width: panel.style.width,
                    height: panel.style.height,
                    left: panel.style.left,
                    top: panel.style.top,
                    transform: panel.style.transform
                }};
                localStorage.setItem('stillme_chat_panel_state', JSON.stringify(state));
            }}
            
            // Initialize
            console.log('StillMe Chat: Initializing...');
            loadPanelState();
            if (!isOpen) {{
                panel.style.display = 'none';
                overlay.style.display = 'none';
            }}
            
            // CRITICAL: Ensure chat button is always visible
            const chatButton = document.getElementById('stillme-chat-button');
            console.log('StillMe Chat: Button element:', chatButton);
            if (chatButton) {{
                chatButton.style.display = 'flex';
                chatButton.style.visibility = 'visible';
                chatButton.style.opacity = '1';
                chatButton.style.zIndex = '2147483647';
                console.log('StillMe Chat: Button styles applied');
                console.log('StillMe Chat: Button position:', chatButton.getBoundingClientRect());
                
                // Try to inject button into parent window if in iframe
                try {{
                    if (window.parent && window.parent !== window) {{
                        console.log('StillMe Chat: Detected iframe, attempting to inject into parent...');
                        const parentDoc = window.parent.document;
                        
                        // Remove existing button if any
                        const existingBtn = parentDoc.getElementById('stillme-chat-button-parent');
                        if (existingBtn) {{
                            existingBtn.remove();
                        }}
                        
                        // Create new button with full styling
                        const clonedButton = parentDoc.createElement('button');
                        clonedButton.id = 'stillme-chat-button-parent';
                        clonedButton.textContent = '💬';
                        clonedButton.innerHTML = '💬';
                        
                        // Apply ALL styles directly (critical for parent window)
                        clonedButton.style.cssText = `
                            position: fixed !important;
                            bottom: 20px !important;
                            right: 20px !important;
                            width: 60px !important;
                            height: 60px !important;
                            border-radius: 50% !important;
                            background: linear-gradient(135deg, #46b3ff 0%, #1e90ff 100%) !important;
                            border: 3px solid #ffffff !important;
                            color: white !important;
                            font-size: 28px !important;
                            cursor: pointer !important;
                            box-shadow: 0 4px 20px rgba(70, 179, 255, 0.6), 0 0 0 4px rgba(70, 179, 255, 0.2) !important;
                            transition: all 0.3s ease !important;
                            display: flex !important;
                            align-items: center !important;
                            justify-content: center !important;
                            z-index: 2147483647 !important;
                            visibility: visible !important;
                            opacity: 1 !important;
                            pointer-events: auto !important;
                            margin: 0 !important;
                            padding: 0 !important;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                        `;
                        
                        clonedButton.onclick = function(e) {{
                            e.preventDefault();
                            e.stopPropagation();
                            console.log('StillMe Chat: Parent button clicked');
                            
                            // Find iframe and send message to it
                            const iframes = parentDoc.querySelectorAll('iframe');
                            console.log('StillMe Chat: Found iframes:', iframes.length);
                            
                            let messageSent = false;
                            for (let iframe of iframes) {{
                                try {{
                                    if (iframe.contentWindow) {{
                                        console.log('StillMe Chat: Sending message to iframe:', iframe.src || 'srcdoc');
                                        iframe.contentWindow.postMessage({{type: 'stillme_toggle_chat'}}, '*');
                                        messageSent = true;
                                    }}
                                }} catch (err) {{
                                    console.warn('StillMe Chat: Could not send to iframe:', err);
                                }}
                            }}
                            
                            if (!messageSent) {{
                                console.error('StillMe Chat: Could not find iframe to send message to');
                            }}
                        }};
                        
                        clonedButton.onmouseenter = function() {{
                            this.style.transform = 'scale(1.15)';
                            this.style.boxShadow = '0 6px 24px rgba(70, 179, 255, 0.8), 0 0 0 6px rgba(70, 179, 255, 0.3)';
                        }};
                        
                        clonedButton.onmouseleave = function() {{
                            this.style.transform = 'scale(1)';
                            this.style.boxShadow = '0 4px 20px rgba(70, 179, 255, 0.6), 0 0 0 4px rgba(70, 179, 255, 0.2)';
                        }};
                        
                        if (parentDoc.body) {{
                            parentDoc.body.appendChild(clonedButton);
                            console.log('StillMe Chat: Button injected into parent window');
                            console.log('StillMe Chat: Parent button position:', clonedButton.getBoundingClientRect());
                        }}
                    }}
                }} catch (e) {{
                    console.warn('StillMe Chat: Could not inject into parent:', e);
                }}
            }} else {{
                console.error('StillMe Chat: Button not found!');
            }}
            
            // Ensure button stays visible even when panel is open
            function ensureButtonVisible() {{
                const btn = document.getElementById('stillme-chat-button');
                if (btn) {{
                    const rect = btn.getBoundingClientRect();
                    if (rect.width === 0 || rect.height === 0) {{
                        console.warn('StillMe Chat: Button has zero dimensions!');
                        btn.style.display = 'flex';
                        btn.style.visibility = 'visible';
                        btn.style.opacity = '1';
                        btn.style.zIndex = '2147483647';
                    }}
                }} else {{
                    console.warn('StillMe Chat: Button not found in ensureButtonVisible()');
                }}
            }}
            
            // Check button visibility periodically
            setInterval(ensureButtonVisible, 1000);
            
            // Listen for messages from parent window
            window.addEventListener('message', function(event) {{
                console.log('StillMe Chat: Received message:', event.data, 'from:', event.origin);
                if (event.data && event.data.type === 'stillme_toggle_chat') {{
                    console.log('StillMe Chat: Toggling chat panel...');
                    toggleChat();
                }}
            }});
            
            // Also expose toggleChat globally for direct access (fallback)
            window.stillmeToggleChat = function() {{
                console.log('StillMe Chat: toggleChat called via global function');
                toggleChat();
            }};
            
            // Render chat history with auto-scroll
            function renderMessages() {{
                const messagesContainer = document.getElementById('stillme-chat-messages');
                messagesContainer.innerHTML = '';
                
                chatHistory.forEach(msg => {{
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `stillme-chat-message ${{msg.role}}`;
                    messageDiv.textContent = msg.content;
                    messagesContainer.appendChild(messageDiv);
                }});
                
                // Auto-scroll to bottom (like ChatGPT, DeepSeek, etc.)
                setTimeout(() => {{
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }}, 10);
            }}
            
            // Toggle chat panel with overlay
            function toggleChat() {{
                console.log('StillMe Chat: toggleChat() called');
                const isVisible = panel.style.display === 'flex';
                console.log('StillMe Chat: Panel currently visible:', isVisible);
                
                panel.style.display = isVisible ? 'none' : 'flex';
                overlay.style.display = isVisible ? 'none' : 'block';
                
                console.log('StillMe Chat: Panel display set to:', panel.style.display);
                console.log('StillMe Chat: Overlay display set to:', overlay.style.display);
                console.log('StillMe Chat: Panel element:', panel);
                console.log('StillMe Chat: Overlay element:', overlay);
                
                // Ensure button stays visible
                ensureButtonVisible();
                
                if (!isVisible) {{
                    // Focus input when opening
                    setTimeout(() => {{
                        const input = document.getElementById('stillme-chat-input');
                        if (input) {{
                            input.focus();
                            console.log('StillMe Chat: Input focused');
                        }} else {{
                            console.warn('StillMe Chat: Input not found');
                        }}
                    }}, 100);
                }}
            }}
            
            // Toggle fullscreen
            function toggleFullscreen() {{
                isFullscreen = !isFullscreen;
                const fullscreenBtn = document.getElementById('fullscreen-btn');
                
                if (isFullscreen) {{
                    panel.classList.add('fullscreen');
                    fullscreenBtn.textContent = '⛶'; // Restore icon
                    fullscreenBtn.title = 'Exit Fullscreen';
                }} else {{
                    panel.classList.remove('fullscreen');
                    fullscreenBtn.textContent = '⛶'; // Fullscreen icon
                    fullscreenBtn.title = 'Toggle Fullscreen';
                    // Restore saved position/size
                    loadPanelState();
                }}
            }}
            
            // Drag functionality
            header.addEventListener('mousedown', (e) => {{
                if (isFullscreen) return; // Don't drag in fullscreen
                isDragging = true;
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                
                const rect = panel.getBoundingClientRect();
                panelStartX = rect.left;
                panelStartY = rect.top;
                
                panel.style.transform = 'none';
                panel.style.left = panelStartX + 'px';
                panel.style.top = panelStartY + 'px';
                
                e.preventDefault();
            }});
            
            // Resize functionality
            function setupResizeHandle(handle, direction) {{
                handle.addEventListener('mousedown', (e) => {{
                    if (isFullscreen) return; // Don't resize in fullscreen
                    isResizing = true;
                    resizeHandle = direction;
                    dragStartX = e.clientX;
                    dragStartY = e.clientY;
                    
                    const rect = panel.getBoundingClientRect();
                    panelStartX = rect.left;
                    panelStartY = rect.top;
                    panelStartWidth = rect.width;
                    panelStartHeight = rect.height;
                    
                    panel.style.transform = 'none';
                    panel.style.left = panelStartX + 'px';
                    panel.style.top = panelStartY + 'px';
                    
                    e.preventDefault();
                    e.stopPropagation();
                }});
            }}
            
            // Setup all resize handles
            setupResizeHandle(document.querySelector('.resize-handle.nw'), 'nw');
            setupResizeHandle(document.querySelector('.resize-handle.ne'), 'ne');
            setupResizeHandle(document.querySelector('.resize-handle.sw'), 'sw');
            setupResizeHandle(document.querySelector('.resize-handle.se'), 'se');
            setupResizeHandle(document.querySelector('.resize-handle.n'), 'n');
            setupResizeHandle(document.querySelector('.resize-handle.s'), 's');
            setupResizeHandle(document.querySelector('.resize-handle.e'), 'e');
            setupResizeHandle(document.querySelector('.resize-handle.w'), 'w');
            
            // Mouse move handler for drag and resize
            document.addEventListener('mousemove', (e) => {{
                if (isDragging && !isFullscreen) {{
                    const deltaX = e.clientX - dragStartX;
                    const deltaY = e.clientY - dragStartY;
                    
                    let newX = panelStartX + deltaX;
                    let newY = panelStartY + deltaY;
                    
                    // Constrain to viewport
                    newX = Math.max(0, Math.min(newX, window.innerWidth - panel.offsetWidth));
                    newY = Math.max(0, Math.min(newY, window.innerHeight - panel.offsetHeight));
                    
                    panel.style.left = newX + 'px';
                    panel.style.top = newY + 'px';
                }} else if (isResizing && !isFullscreen && resizeHandle) {{
                    const deltaX = e.clientX - dragStartX;
                    const deltaY = e.clientY - dragStartY;
                    
                    let newWidth = panelStartWidth;
                    let newHeight = panelStartHeight;
                    let newX = panelStartX;
                    let newY = panelStartY;
                    
                    // Handle different resize directions
                    if (resizeHandle.includes('e')) {{
                        newWidth = Math.max(400, panelStartWidth + deltaX);
                    }}
                    if (resizeHandle.includes('w')) {{
                        newWidth = Math.max(400, panelStartWidth - deltaX);
                        newX = panelStartX + deltaX;
                    }}
                    if (resizeHandle.includes('s')) {{
                        newHeight = Math.max(400, panelStartHeight + deltaY);
                    }}
                    if (resizeHandle.includes('n')) {{
                        newHeight = Math.max(400, panelStartHeight - deltaY);
                        newY = panelStartY + deltaY;
                    }}
                    
                    // Constrain to viewport
                    newWidth = Math.min(newWidth, window.innerWidth - newX);
                    newHeight = Math.min(newHeight, window.innerHeight - newY);
                    
                    panel.style.width = newWidth + 'px';
                    panel.style.height = newHeight + 'px';
                    panel.style.left = newX + 'px';
                    panel.style.top = newY + 'px';
                }}
            }});
            
            // Mouse up handler
            document.addEventListener('mouseup', () => {{
                if (isDragging || isResizing) {{
                    savePanelState();
                }}
                isDragging = false;
                isResizing = false;
                resizeHandle = null;
            }});
            
            // Send message
            async function sendMessage() {{
                const input = document.getElementById('stillme-chat-input');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Disable send button
                const sendBtn = document.getElementById('stillme-chat-send');
                sendBtn.disabled = true;
                sendBtn.textContent = 'Sending...';
                
                // Add user message to history
                chatHistory.push({{ role: 'user', content: message }});
                renderMessages();
                
                // Clear input
                input.value = '';
                
                // Send to backend
                try {{
                    const response = await fetch(`${{API_BASE}}/api/chat/smart_router`, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{ message: message }}),
                    }});
                    
                    const data = await response.json();
                    const reply = data.response || data.message || JSON.stringify(data);
                    
                    // Add assistant response
                    chatHistory.push({{ role: 'assistant', content: reply }});
                    renderMessages();
                    
                    // Send message to Streamlit parent
                    window.parent.postMessage({{
                        type: 'stillme_chat_message',
                        history: chatHistory
                    }}, '*');
                    
                }} catch (error) {{
                    chatHistory.push({{ 
                        role: 'assistant', 
                        content: `❌ Error: ${{error.message}}` 
                    }});
                    renderMessages();
                }} finally {{
                    sendBtn.disabled = false;
                    sendBtn.textContent = 'Send';
                    input.focus();
                }}
            }}
            
            // Handle Enter key (Enter to send, Shift+Enter for new line)
            document.getElementById('stillme-chat-input').addEventListener('keydown', (e) => {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    sendMessage();
                }}
            }});
            
            // Initial render
            renderMessages();
        </script>
    </body>
    </html>
    """
    
    # CRITICAL: Use height=0 to allow full viewport control
    # Note: components.html() doesn't support 'key' parameter
    return components.html(html_content, height=0)

