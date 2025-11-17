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
                min-width: 300px !important; /* Reduced for better screenshot capability */
                min-height: 300px !important; /* Reduced for better screenshot capability */
                max-width: 95vw !important;
                max-height: 95vh !important;
                background: #1e1e1e !important; /* Cursor-like dark background */
                border-radius: 8px !important; /* Smaller radius like Cursor */
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1) !important; /* Subtle shadow like Cursor */
                display: {'flex' if is_open else 'none'} !important;
                flex-direction: column !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important; /* Subtle border like Cursor */
                overflow: hidden !important;
                resize: none !important; /* Disable browser native resize - we use custom handles */
                z-index: 1000000 !important;
                /* CRITICAL: Ensure proper flex layout */
                align-items: stretch !important;
                /* CRITICAL: Enable dragging */
                cursor: default !important;
            }}
            
            /* Dragging state */
            #stillme-chat-panel.dragging {{
                cursor: move !important;
                user-select: none !important;
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
            
            /* Minimized mode - chỉ hiển thị header */
            #stillme-chat-panel.minimized {{
                height: auto !important;
                min-height: auto !important;
                max-height: 60px !important;
            }}
            
            #stillme-chat-panel.minimized .stillme-chat-messages,
            #stillme-chat-panel.minimized .stillme-chat-input-container {{
                display: none !important;
            }}
            
            /* Force visible class (fallback if inline style doesn't work) */
            #stillme-chat-panel.force-visible {{
                display: flex !important;
                visibility: visible !important;
                opacity: 1 !important;
            }}
            
            #stillme-chat-overlay.force-visible {{
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
            }}
            
            /* Resize handles - 8 handles (4 corners + 4 edges) - Cursor style */
            .resize-handle {{
                position: absolute;
                background: transparent;
                z-index: 1000001 !important; /* CRITICAL: Higher than panel z-index (1000000) to ensure it's always on top */
                pointer-events: auto !important; /* Ensure handles are clickable */
                user-select: none !important; /* Prevent text selection when resizing */
            }}
            
            /* Corner handles - larger for easier grabbing (increased for better UX) */
            .resize-handle.nw {{ top: 0; left: 0; width: 24px; height: 24px; cursor: nw-resize; }}
            .resize-handle.ne {{ top: 0; right: 0; width: 24px; height: 24px; cursor: ne-resize; }}
            .resize-handle.sw {{ bottom: 0; left: 0; width: 24px; height: 24px; cursor: sw-resize; }}
            .resize-handle.se {{ bottom: 0; right: 0; width: 24px; height: 24px; cursor: se-resize; }}
            
            /* Edge handles - wider for easier grabbing (increased for better UX) */
            .resize-handle.n {{ top: 0; left: 24px; right: 24px; height: 16px; cursor: n-resize; }}
            .resize-handle.s {{ bottom: 0; left: 24px; right: 24px; height: 16px; cursor: s-resize; }}
            .resize-handle.e {{ top: 24px; bottom: 24px; right: 0; width: 16px; cursor: e-resize; }}
            .resize-handle.w {{ top: 24px; bottom: 24px; left: 0; width: 16px; cursor: w-resize; }}
            
            /* CRITICAL: Fix scrollbar vs resize handle conflict */
            /* Problem: Resize handle .e (right edge, 16px wide) overlaps with scrollbar (6px wide) */
            /* Solution: JavaScript detects scrollbar area (rightmost 12px) and skips resize if click is in that area */
            /* CSS: Ensure scrollbar is interactive */
            .stillme-chat-messages::-webkit-scrollbar {{
                pointer-events: auto !important; /* Ensure scrollbar captures events */
            }}
            
            /* Visual resize indicator - more visible like Cursor */
            .resize-handle:hover {{
                background: rgba(70, 179, 255, 0.5) !important; /* More visible on hover */
            }}
            
            /* Show resize handles more clearly - add subtle border on hover */
            .resize-handle:hover::after {{
                content: '';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 4px;
                height: 4px;
                background: rgba(70, 179, 255, 0.8);
                border-radius: 50%;
            }}
            
            /* Edge handles show double arrow on hover */
            .resize-handle.n:hover::after,
            .resize-handle.s:hover::after {{
                content: '⇅';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: rgba(70, 179, 255, 0.9);
                font-size: 14px;
                width: auto;
                height: auto;
            }}
            
            .resize-handle.e:hover::after,
            .resize-handle.w:hover::after {{
                content: '⇄';
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                color: rgba(70, 179, 255, 0.9);
                font-size: 14px;
                width: auto;
                height: auto;
            }}
            
            /* Disable resize when minimized or fullscreen */
            #stillme-chat-panel.minimized .resize-handle,
            #stillme-chat-panel.fullscreen .resize-handle {{
                display: none !important;
            }}
            
            .stillme-chat-header {{
                background: #252526 !important; /* Cursor-like header background */
                padding: 12px 16px !important; /* Tighter padding like Cursor */
                border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important; /* Subtle border */
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
                cursor: move !important; /* Indicate draggable */
                user-select: none !important; /* Prevent text selection when dragging */
                flex-shrink: 0 !important; /* Don't shrink header */
                order: 1 !important; /* Header first */
            }}
            
            .stillme-chat-header h3 {{
                margin: 0;
                color: #cccccc !important; /* Cursor-like text color */
                font-size: 14px !important; /* Smaller font like Cursor */
                font-weight: 500 !important; /* Medium weight like Cursor */
            }}
            
            #stillme-chat-status {{
                color: #858585 !important;
                font-size: 11px !important;
                font-style: italic !important;
                margin-top: 4px !important;
                white-space: nowrap !important;
                overflow: hidden !important;
                text-overflow: ellipsis !important;
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
                flex: 1 1 auto !important; /* Take available space */
                overflow-y: auto !important;
                padding: 16px !important; /* Tighter padding like Cursor */
                display: flex !important;
                flex-direction: column !important;
                gap: 12px !important;
                background: #1e1e1e !important; /* Match panel background */
                min-height: 0 !important; /* CRITICAL: Allow flex item to shrink */
                order: 2 !important; /* Messages second */
            }}
            
            .stillme-chat-message {{
                padding: 10px 14px !important; /* Tighter padding like Cursor */
                border-radius: 6px !important; /* Smaller radius like Cursor */
                max-width: 80%;
                word-wrap: break-word;
                line-height: 1.6 !important; /* Better line height for readability */
            }}
            
            .stillme-chat-message.assistant {{
                /* Markdown support for assistant messages */
                /* HTML rendering with <p>, <br>, <strong>, <ul>, <h2>, <h3>, <table> */
            }}
            
            .stillme-chat-message.assistant p {{
                margin: 8px 0 !important; /* Spacing for p tags */
            }}
            
            .stillme-chat-message.assistant h2 {{
                margin: 16px 0 8px 0 !important;
                font-size: 1.2em !important;
                font-weight: 600 !important;
                color: #cccccc !important;
            }}
            
            .stillme-chat-message.assistant h3 {{
                margin: 12px 0 6px 0 !important;
                font-size: 1.1em !important;
                font-weight: 600 !important;
                color: #cccccc !important;
            }}
            
            .stillme-chat-message.assistant ul {{
                margin: 8px 0 !important;
                padding-left: 20px !important;
            }}
            
            .stillme-chat-message.assistant li {{
                margin: 4px 0 !important;
            }}
            
            .stillme-chat-message.assistant strong {{
                font-weight: 600 !important;
                color: #ffffff !important;
            }}
            
            .stillme-chat-message.user {{
                background: #0e639c !important; /* Cursor-like blue */
                color: #ffffff !important;
                align-self: flex-end;
                margin-left: auto;
            }}
            
            .stillme-chat-message.assistant {{
                background: #2d2d30 !important; /* Cursor-like dark gray */
                color: #cccccc !important; /* Cursor-like text color */
                align-self: flex-start;
            }}
            
            .stillme-chat-input-container {{
                padding: 12px 16px !important; /* Tighter padding like Cursor */
                border-top: 1px solid rgba(255, 255, 255, 0.15) !important; /* More visible border to separate from messages */
                background: #252526 !important; /* Slightly different background like Cursor */
                flex-shrink: 0 !important; /* Don't shrink input area */
                flex-grow: 0 !important; /* Don't grow */
                order: 3 !important; /* Input last (at bottom) */
                margin-top: auto !important; /* Push to bottom - CRITICAL */
            }}
            
            .stillme-chat-input-wrapper {{
                display: flex;
                gap: 8px;
            }}
            
            #stillme-chat-input {{
                flex: 1;
                padding: 10px 14px !important; /* Tighter padding like Cursor */
                background: #2d2d30 !important; /* Cursor-like input background */
                border: 1px solid rgba(255, 255, 255, 0.1) !important; /* Subtle border */
                border-radius: 4px !important; /* Smaller radius like Cursor */
                color: #cccccc !important; /* Cursor-like text color */
                font-size: 14px !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                resize: none;
            }}
            
            #stillme-chat-input:focus {{
                outline: none !important;
                border-color: #0e639c !important; /* Cursor-like focus color */
            }}
            
            #stillme-chat-input::placeholder {{
                color: #858585 !important; /* Cursor-like placeholder color */
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
                    <div style="flex: 1; min-width: 0;">
                        <h3>💬 Chat with StillMe</h3>
                        <div id="stillme-chat-status" style="font-size: 11px; color: #858585; margin-top: 4px; display: none; font-style: italic;"></div>
                    </div>
                    <div class="stillme-chat-header-buttons">
                        <button class="stillme-chat-header-btn" id="minimize-btn" onclick="toggleMinimize()" title="Minimize">−</button>
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
            // Wrap everything in try-catch to prevent silent failures
            try {{
                console.log('StillMe Chat: Script starting...');
                
            const API_BASE = '{api_base}';
            let chatHistory = {chat_history_json};
            let isOpen = {str(is_open).lower()};
            
                console.log('StillMe Chat: Variables initialized, isOpen:', isOpen);
                
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
                
                // Wait for DOM to be ready
                function initChat() {{
                    console.log('StillMe Chat: Initializing chat widget...');
                    
                    // Get panel element
                    const panel = document.getElementById('stillme-chat-panel');
                    const overlay = document.getElementById('stillme-chat-overlay');
                    const header = document.getElementById('stillme-chat-header');
                    
                    console.log('StillMe Chat: Panel element:', panel);
                    console.log('StillMe Chat: Overlay element:', overlay);
                    console.log('StillMe Chat: Header element:', header);
                    
                    if (!panel) {{
                        console.error('StillMe Chat: Panel element not found!');
                        return;
                    }}
                    if (!overlay) {{
                        console.error('StillMe Chat: Overlay element not found!');
                        return;
                    }}
            
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
                                console.warn('StillMe Chat: Failed to load panel state:', e);
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
                    console.log('StillMe Chat: Loading panel state...');
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
                                                
                                                // Method 1: Try postMessage
                                                try {{
                                                    iframe.contentWindow.postMessage({{type: 'stillme_toggle_chat'}}, '*');
                                                    messageSent = true;
                                                    console.log('StillMe Chat: Message sent via postMessage');
                                                }} catch (postErr) {{
                                                    console.warn('StillMe Chat: postMessage failed:', postErr);
                                                }}
                                                
                                                // Method 2: Try direct function call (fallback)
                                                try {{
                                                    if (iframe.contentWindow.stillmeToggleChat) {{
                                                        console.log('StillMe Chat: Calling stillmeToggleChat directly');
                                                        iframe.contentWindow.stillmeToggleChat();
                                                        messageSent = true;
                                                    }}
                                                }} catch (directErr) {{
                                                    console.warn('StillMe Chat: Direct call failed:', directErr);
                                                }}
                                                
                                                // Method 3: Try accessing toggleChat via iframe window
                                                try {{
                                                    // Access the iframe's window and call toggleChat if available
                                                    const iframeWindow = iframe.contentWindow;
                                                    if (iframeWindow && typeof iframeWindow.toggleChat === 'function') {{
                                                        console.log('StillMe Chat: Calling toggleChat via iframe window');
                                                        iframeWindow.toggleChat();
                                                        messageSent = true;
                                                    }}
                                                }} catch (windowErr) {{
                                                    console.warn('StillMe Chat: Window access failed:', windowErr);
                                                }}
                                            }}
                                        }} catch (err) {{
                                            console.warn('StillMe Chat: Could not access iframe:', err);
                                        }}
                                    }}
                                    
                                    if (!messageSent) {{
                                        console.error('StillMe Chat: Could not find iframe to send message to');
                                        console.error('StillMe Chat: All communication methods failed');
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
                    
                    // Listen for messages from parent window (register early)
                    window.addEventListener('message', function(event) {{
                        console.log('StillMe Chat: Received message:', event.data, 'from:', event.origin);
                        if (event.data && event.data.type === 'stillme_toggle_chat') {{
                            console.log('StillMe Chat: Toggling chat panel...');
                            toggleChat();
                        }} else if (event.data && event.data.type === 'stillme_send_message') {{
                            // Handle message sent from parent panel
                            console.log('StillMe Chat: Received send message request from parent');
                            const message = event.data.message;
                            if (message) {{
                                // CRITICAL: Call sendMessageFromParent to avoid CORS (API call in iframe context)
                                sendMessageFromParent(message);
                            }}
                        }}
                    }}, false); // Use capture phase for earlier registration
                    
                    // Also expose toggleChat globally for direct access (fallback)
                    window.stillmeToggleChat = function() {{
                        console.log('StillMe Chat: toggleChat called via global function');
                        toggleChat();
                    }};
                    
                    // Expose toggleChat on window for direct access
                    window.toggleChat = toggleChat;
                    
                    console.log('StillMe Chat: Message listener registered and toggleChat exposed globally');
                    
                    // Simple markdown to HTML converter (preserves line breaks and renders basic markdown)
            function markdownToHtml(text) {{
                if (!text) return '';
                
                let html = String(text);
                
                // CRITICAL: Preserve line breaks first
                // Convert double newlines to p tags, single newlines to br tags
                html = html.replace(new RegExp('\\n\\n+', 'g'), '</p><p>');
                html = '<p>' + html + '</p>';
                html = html.replace(new RegExp('\\n', 'g'), '<br>');
                
                // Headers: ## Header -> <h2>Header</h2>
                var h3Pattern = new RegExp('<p>### (.+?)</p>', 'g');
                html = html.replace(h3Pattern, '<h3>$1</h3>');
                var h2Pattern = new RegExp('<p>## (.+?)</p>', 'g');
                html = html.replace(h2Pattern, '<h2>$1</h2>');
                
                // Bold: **text** -> <strong>text</strong>
                // CRITICAL: In Python f-string, \\\\* becomes \\* in JavaScript string, which becomes \* in regex
                // Need 4 backslashes in Python f-string to get 2 backslashes in JS string, which becomes 1 backslash in regex
                var boldPattern = new RegExp('\\\\*\\\\*([^*]+?)\\\\*\\\\*', 'g');
                html = html.replace(boldPattern, '<strong>$1</strong>');
                
                // Bullet points: - item -> <li>item</li>
                var bulletPattern = new RegExp('<p>- (.+?)</p>', 'g');
                html = html.replace(bulletPattern, '<li>$1</li>');
                // Wrap consecutive <li> in <ul>
                // In Python f-string, \\\\s becomes \\s in JavaScript string, which becomes \s in regex
                var listPattern = new RegExp('(<li>.*?</li>\\\\s*)+', 'g');
                html = html.replace(listPattern, function(match) {{
                    return '<ul style="margin: 8px 0; padding-left: 20px;">' + match + '</ul>';
                }});
                
                // Tables: | col1 | col2 | -> <table>...
                // In Python f-string, \\\\| becomes \\| in JavaScript string, which becomes \| in regex
                // In Python f-string, \\\\s becomes \\s in JavaScript string, which becomes \s in regex
                var tablePattern = new RegExp('<p>\\\\|(.+?)\\\\|</p>\\\\s*<p>\\\\|([-| ]+?)\\\\|</p>\\\\s*((?:<p>\\\\|.+?\\\\|</p>\\\\s*)+)', 'g');
                html = html.replace(tablePattern, function(match, header, separator, rows) {{
                    var headers = header.split('|').map(function(h) {{ return h.trim(); }}).filter(function(h) {{ return h; }});
                    var rowLines = rows.match(new RegExp('<p>\\\\|.+?\\\\|</p>', 'g')) || [];
                    var rowData = rowLines.map(function(row) {{
                        return row.replace(new RegExp('</?p>', 'g'), '').split('|').map(function(c) {{ return c.trim(); }}).filter(function(c) {{ return c; }});
                    }});
                    
                    var tableHtml = '<table style="border-collapse: collapse; margin: 10px 0; width: 100%;"><thead><tr>';
                    headers.forEach(function(h) {{
                        tableHtml += '<th style="border: 1px solid #555; padding: 8px; text-align: left; background: #2d2d30;">' + h + '</th>';
                    }});
                    tableHtml += '</tr></thead><tbody>';
                    rowData.forEach(function(row) {{
                        tableHtml += '<tr>';
                        row.forEach(function(cell) {{
                            tableHtml += '<td style="border: 1px solid #555; padding: 8px;">' + cell + '</td>';
                        }});
                        tableHtml += '</tr>';
                    }});
                    tableHtml += '</tbody></table>';
                    return tableHtml;
                }});
                
                // Clean up empty p tags
                var emptyP = new RegExp('<p></p>', 'g');
                html = html.replace(emptyP, '');
                var blockP = new RegExp('<p>(<[^>]+>)</p>', 'g');
                html = html.replace(blockP, '$1'); // Remove p tags around block elements
                
                return html;
            }}
            
                    // Render chat history with auto-scroll
            function renderMessages() {{
                console.log('StillMe Chat: renderMessages() called, chatHistory length:', chatHistory.length);
                const messagesContainer = document.getElementById('stillme-chat-messages');
                if (!messagesContainer) {{
                    console.error('StillMe Chat: messagesContainer not found!');
                    return;
                }}
                messagesContainer.innerHTML = '';
                
                chatHistory.forEach((msg, index) => {{
                    console.log('StillMe Chat: Rendering message', index, 'role:', msg.role, 'content length:', msg.content ? msg.content.length : 0);
                    const messageDiv = document.createElement('div');
                    messageDiv.className = `stillme-chat-message ${{msg.role}}`;
                    
                    // CRITICAL: Use innerHTML with markdown conversion for assistant messages
                    // This preserves line breaks and renders markdown (**, ##, -, tables)
                    if (msg.role === 'assistant') {{
                        messageDiv.innerHTML = markdownToHtml(msg.content);
                    }} else {{
                        // User messages: plain text (escape HTML for security)
                        messageDiv.textContent = msg.content;
                    }}
                    
                    // Add feedback buttons for assistant messages
                    if (msg.role === 'assistant' && msg.message_id) {{
                        const feedbackDiv = document.createElement('div');
                        feedbackDiv.className = 'stillme-feedback-buttons';
                        
                        const likeBtn = document.createElement('button');
                        likeBtn.className = 'stillme-feedback-btn';
                        likeBtn.innerHTML = '👍 Like';
                        likeBtn.onclick = () => submitFeedback(msg.message_id, msg.question || '', msg.content, 1);
                        
                        const dislikeBtn = document.createElement('button');
                        dislikeBtn.className = 'stillme-feedback-btn';
                        dislikeBtn.innerHTML = '👎 Dislike';
                        dislikeBtn.onclick = () => submitFeedback(msg.message_id, msg.question || '', msg.content, -1);
                        
                        feedbackDiv.appendChild(likeBtn);
                        feedbackDiv.appendChild(dislikeBtn);
                        messageDiv.appendChild(feedbackDiv);
                    }}
                    
                    messagesContainer.appendChild(messageDiv);
                }});
                
                        // Auto-scroll to bottom (like ChatGPT, DeepSeek, etc.)
                        setTimeout(() => {{
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                        }}, 10);
            }}
            
            // Submit feedback (like/dislike)
            async function submitFeedback(messageId, question, response, rating) {{
                try {{
                    const response_data = await fetch(`${{API_BASE}}/api/feedback/submit`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            message_id: messageId,
                            question: question,
                            response: response,
                            rating: rating,
                        }}),
                    }});
                    
                    if (response_data.ok) {{
                        const data = await response_data.json();
                        console.log('Feedback submitted:', data);
                        
                        // Update button state
                        const buttons = document.querySelectorAll(`[data-message-id="${{messageId}}"]`);
                        buttons.forEach(btn => {{
                            if (rating === 1) {{
                                btn.classList.add('liked');
                            }} else {{
                                btn.classList.add('disliked');
                            }}
                        }});
                    }}
                }} catch (error) {{
                    console.error('Error submitting feedback:', error);
                }}
            }}
            
                    // Toggle chat panel with overlay
            function toggleChat() {{
                        console.log('StillMe Chat: toggleChat() called');
                        const isVisible = panel.style.display === 'flex' || panel.style.display === '';
                        console.log('StillMe Chat: Panel currently visible:', isVisible);
                        console.log('StillMe Chat: Panel computed style before:', window.getComputedStyle(panel).display);
                        
                        // CRITICAL: If in iframe, also inject panel into parent window
                        if (window.parent && window.parent !== window) {{
                            const parentDoc = window.parent.document;
                            const parentWindow = window.parent; // CRITICAL: Define parentWindow for event listeners
                            let parentPanel = parentDoc.getElementById('stillme-chat-panel-parent');
                            let parentOverlay = parentDoc.getElementById('stillme-chat-overlay-parent');
                            
                            if (!isVisible) {{
                                // Hide iframe panel when parent panel is shown (fix double input issue)
                                panel.style.setProperty('display', 'none', 'important');
                                
                                // Open panel - create in parent if doesn't exist
                                if (!parentPanel) {{
                                    console.log('StillMe Chat: Creating panel in parent window...');
                                    
                                    // Create overlay in parent
                                    parentOverlay = parentDoc.createElement('div');
                                    parentOverlay.id = 'stillme-chat-overlay-parent';
                                    parentOverlay.style.cssText = `
                                        position: fixed !important;
                                        top: 0 !important;
                                        left: 0 !important;
                                        width: 100vw !important;
                                        height: 100vh !important;
                                        background: rgba(0, 0, 0, 0.3) !important;
                                        z-index: 999999 !important;
                                        display: block !important;
                                    `;
                                    parentOverlay.onclick = function() {{
                                        const iframes = parentDoc.querySelectorAll('iframe');
                                        for (let iframe of iframes) {{
                                            try {{
                                                if (iframe.contentWindow) {{
                                                    iframe.contentWindow.postMessage({{type: 'stillme_toggle_chat'}}, '*');
                                                }}
                                            }} catch (e) {{
                                                console.warn('StillMe Chat: Could not send toggle message:', e);
                                            }}
                                        }}
                                    }};
                                    
                                    // CRITICAL: Inject CSS styles into parent window first
                                    if (!parentDoc.getElementById('stillme-chat-styles')) {{
                                        const styleSheet = parentDoc.createElement('style');
                                        styleSheet.id = 'stillme-chat-styles';
                                        styleSheet.textContent = `
                                            #stillme-chat-panel-parent {{
                                                position: fixed !important;
                                                top: 50%; /* No !important - allow inline style override for drag/resize */
                                                left: 50%; /* No !important - allow inline style override for drag/resize */
                                                transform: translate(-50%, -50%) !important;
                                                width: 600px; /* No !important - allow inline style override for resize */
                                                height: 700px; /* No !important - allow inline style override for resize */
                                                min-width: 300px !important; /* Reduced for better screenshot capability */
                                                min-height: 300px !important; /* Reduced for better screenshot capability */
                                                max-width: 95vw !important;
                                                max-height: 95vh !important;
                                                background: #1e1e1e !important;
                                                border-radius: 8px !important;
                                                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1) !important;
                                                display: flex !important;
                                                flex-direction: column !important;
                                                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                                                overflow: hidden !important;
                                                z-index: 1000000 !important;
                                                align-items: stretch !important;
                                            }}
                                            #stillme-chat-panel-parent .stillme-chat-header {{
                                                background: #252526 !important;
                                                padding: 12px 16px !important;
                                                border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
                                                display: flex !important;
                                                justify-content: space-between !important;
                                                align-items: center !important;
                                                cursor: move !important;
                                                user-select: none !important;
                                                flex-shrink: 0 !important;
                                                order: 1 !important;
                                            }}
                                            #stillme-chat-panel-parent .stillme-chat-header h3 {{
                                                margin: 0;
                                                color: #cccccc !important;
                                                font-size: 14px !important;
                                                font-weight: 500 !important;
                                                flex: 1;
                                            }}
                                            #stillme-chat-panel-parent #stillme-chat-status {{
                                                color: #858585 !important;
                                                font-size: 11px !important;
                                                font-style: italic !important;
                                                margin-top: 4px !important;
                                            }}
                                            #stillme-chat-panel-parent .resize-handle {{
                                                position: absolute !important;
                                                z-index: 1000001 !important;
                                                pointer-events: auto !important;
                                            }}
                                            #stillme-chat-panel-parent .resize-handle.nw {{ top: 0 !important; left: 0 !important; width: 24px !important; height: 24px !important; cursor: nw-resize !important; }}
                                            #stillme-chat-panel-parent .resize-handle.ne {{ top: 0 !important; right: 0 !important; width: 24px !important; height: 24px !important; cursor: ne-resize !important; }}
                                            #stillme-chat-panel-parent .resize-handle.sw {{ bottom: 0 !important; left: 0 !important; width: 24px !important; height: 24px !important; cursor: sw-resize !important; }}
                                            #stillme-chat-panel-parent .resize-handle.se {{ bottom: 0 !important; right: 0 !important; width: 24px !important; height: 24px !important; cursor: se-resize !important; }}
                                            #stillme-chat-panel-parent .resize-handle.n {{ top: 0 !important; left: 24px !important; right: 24px !important; height: 16px !important; cursor: n-resize !important; }}
                                            #stillme-chat-panel-parent .resize-handle.s {{ bottom: 0 !important; left: 24px !important; right: 24px !important; height: 16px !important; cursor: s-resize !important; }}
                                            #stillme-chat-panel-parent .resize-handle.e {{ top: 24px !important; bottom: 24px !important; right: 0 !important; width: 16px !important; cursor: e-resize !important; }}
                                            #stillme-chat-panel-parent .resize-handle.w {{ top: 24px !important; bottom: 24px !important; left: 0 !important; width: 16px !important; cursor: w-resize !important; }}
                                            #stillme-chat-panel-parent .stillme-chat-messages {{
                                                flex: 1 1 auto !important;
                                                overflow-y: auto !important;
                                                padding: 16px !important;
                                                display: flex !important;
                                                flex-direction: column !important;
                                                gap: 12px !important;
                                                background: #1e1e1e !important;
                                                min-height: 0 !important;
                                                order: 2 !important;
                                            }}
                                            #stillme-chat-panel-parent .stillme-chat-input-container {{
                                                padding: 12px 16px !important;
                                                border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
                                                background: #252526 !important;
                                                flex-shrink: 0 !important;
                                                flex-grow: 0 !important;
                                                order: 3 !important;
                                                margin-top: auto !important;
                                            }}
                                            #stillme-chat-panel-parent .stillme-chat-input-wrapper {{
                                                display: flex;
                                                gap: 8px;
                                            }}
                                            #stillme-chat-panel-parent #stillme-chat-input {{
                                                flex: 1;
                                                padding: 10px 14px !important;
                                                background: #2d2d30 !important;
                                                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                                                border-radius: 4px !important;
                                                color: #cccccc !important;
                                                font-size: 14px !important;
                                                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
                                                resize: none;
                                            }}
                                            #stillme-chat-panel-parent #stillme-chat-input:focus {{
                                                outline: none !important;
                                                border-color: #0e639c !important;
                                            }}
                                            #stillme-chat-panel-parent #stillme-chat-input::placeholder {{
                                                color: #858585 !important;
                                            }}
                                            #stillme-chat-panel-parent #stillme-chat-send {{
                                                padding: 12px 24px;
                                                background: #46b3ff;
                                                border: none;
                                                border-radius: 8px;
                                                color: white;
                                                font-weight: 600;
                                                cursor: pointer;
                                                transition: background 0.2s;
                                            }}
                                            #stillme-chat-panel-parent #stillme-chat-send:hover {{
                                                background: #1e90ff;
                                            }}
                                            #stillme-chat-panel-parent .stillme-chat-message {{
                                                padding: 10px 14px !important;
                                                border-radius: 6px !important;
                                                max-width: 80%;
                                                word-wrap: break-word;
                                                line-height: 1.5 !important;
                                            }}
                                            #stillme-chat-panel-parent .stillme-chat-message.user {{
                                                background: #0e639c !important;
                                                color: #ffffff !important;
                                                align-self: flex-end;
                                                margin-left: auto;
                                            }}
                                            #stillme-chat-panel-parent .stillme-chat-message.assistant {{
                                                background: #2d2d30 !important;
                                                color: #cccccc !important;
                                                align-self: flex-start;
                                            }}
                                            
                                            #stillme-chat-panel-parent .stillme-chat-message.assistant p {{
                                                margin: 8px 0 !important;
                                            }}
                                            
                                            #stillme-chat-panel-parent .stillme-chat-message.assistant h2 {{
                                                margin: 16px 0 8px 0 !important;
                                                font-size: 1.2em !important;
                                                font-weight: 600 !important;
                                                color: #cccccc !important;
                                            }}
                                            
                                            #stillme-chat-panel-parent .stillme-chat-message.assistant h3 {{
                                                margin: 12px 0 6px 0 !important;
                                                font-size: 1.1em !important;
                                                font-weight: 600 !important;
                                                color: #cccccc !important;
                                            }}
                                            
                                            #stillme-chat-panel-parent .stillme-chat-message.assistant ul {{
                                                margin: 8px 0 !important;
                                                padding-left: 20px !important;
                                            }}
                                            
                                            #stillme-chat-panel-parent .stillme-chat-message.assistant li {{
                                                margin: 4px 0 !important;
                                            }}
                                            
                                            #stillme-chat-panel-parent .stillme-chat-message.assistant strong {{
                                                font-weight: 600 !important;
                                                color: #ffffff !important;
                                            }}
            
            /* Feedback buttons (like/dislike) */
            .stillme-feedback-buttons {{
                display: flex !important;
                gap: 8px !important;
                margin-top: 8px !important;
                padding-top: 8px !important;
                border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
            }}
            
            .stillme-feedback-btn {{
                padding: 6px 12px !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 4px !important;
                background: transparent !important;
                color: #cccccc !important;
                cursor: pointer !important;
                font-size: 12px !important;
                transition: all 0.2s !important;
                display: flex !important;
                align-items: center !important;
                gap: 4px !important;
            }}
            
            .stillme-feedback-btn:hover {{
                background: rgba(255, 255, 255, 0.1) !important;
                border-color: rgba(255, 255, 255, 0.3) !important;
            }}
            
            .stillme-feedback-btn.liked {{
                background: rgba(70, 179, 255, 0.2) !important;
                border-color: #46b3ff !important;
                color: #46b3ff !important;
            }}
            
            .stillme-feedback-btn.disliked {{
                background: rgba(255, 100, 100, 0.2) !important;
                border-color: #ff6464 !important;
                color: #ff6464 !important;
            }}
                                        `;
                                        parentDoc.head.appendChild(styleSheet);
                                        console.log('StillMe Chat: CSS styles injected into parent window');
                                    }}
                                    
                                    // Create panel in parent with full HTML structure
                                    // CRITICAL: Create elements in correct order (header -> messages -> input)
                                    parentPanel = parentDoc.createElement('div');
                                    parentPanel.id = 'stillme-chat-panel-parent';
                                    
                                    // Create header
                                    const parentHeader = parentDoc.createElement('div');
                                    parentHeader.className = 'stillme-chat-header';
                                    parentHeader.id = 'stillme-chat-header-parent';
                                    const headerTitleDiv = parentDoc.createElement('div');
                                    headerTitleDiv.style.cssText = 'flex: 1; min-width: 0;';
                                    const headerTitle = parentDoc.createElement('h3');
                                    headerTitle.textContent = '💬 Chat with StillMe';
                                    const parentStatusDiv = parentDoc.createElement('div');
                                    parentStatusDiv.id = 'stillme-chat-status-parent';
                                    parentStatusDiv.style.cssText = 'font-size: 11px; color: #858585; margin-top: 4px; display: none; font-style: italic;';
                                    headerTitleDiv.appendChild(headerTitle);
                                    headerTitleDiv.appendChild(parentStatusDiv);
                                    const headerButtons = parentDoc.createElement('div');
                                    headerButtons.className = 'stillme-chat-header-buttons';
                                    
                                    const minimizeBtn = parentDoc.createElement('button');
                                    minimizeBtn.className = 'stillme-chat-header-btn';
                                    minimizeBtn.id = 'minimize-btn';
                                    minimizeBtn.textContent = '−';
                                    minimizeBtn.title = 'Minimize';
                                    
                                    const fullscreenBtn = parentDoc.createElement('button');
                                    fullscreenBtn.className = 'stillme-chat-header-btn';
                                    fullscreenBtn.id = 'fullscreen-btn';
                                    fullscreenBtn.textContent = '⛶';
                                    fullscreenBtn.title = 'Toggle Fullscreen';
                                    
                                    const closeBtn = parentDoc.createElement('button');
                                    closeBtn.className = 'stillme-chat-close';
                                    closeBtn.textContent = '×';
                                    closeBtn.title = 'Close';
                                    
                                    headerButtons.appendChild(minimizeBtn);
                                    headerButtons.appendChild(fullscreenBtn);
                                    headerButtons.appendChild(closeBtn);
                                    parentHeader.appendChild(headerTitleDiv);
                                    parentHeader.appendChild(headerButtons);
                                    
                                    // Create messages container
                                    const parentMessages = parentDoc.createElement('div');
                                    parentMessages.className = 'stillme-chat-messages';
                                    parentMessages.id = 'stillme-chat-messages';
                                    
                                    // Create input container
                                    const parentInputContainer = parentDoc.createElement('div');
                                    parentInputContainer.className = 'stillme-chat-input-container';
                                    const parentInputWrapper = parentDoc.createElement('div');
                                    parentInputWrapper.className = 'stillme-chat-input-wrapper';
                                    const parentInput = parentDoc.createElement('textarea');
                                    parentInput.id = 'stillme-chat-input';
                                    parentInput.placeholder = 'Type your message... (Press Enter to send, Shift+Enter for new line)';
                                    parentInput.rows = 2;
                                    const parentSendBtn = parentDoc.createElement('button');
                                    parentSendBtn.id = 'stillme-chat-send';
                                    parentSendBtn.textContent = 'Send';
                                    
                                    parentInputWrapper.appendChild(parentInput);
                                    parentInputWrapper.appendChild(parentSendBtn);
                                    parentInputContainer.appendChild(parentInputWrapper);
                                    
                                    // Append in correct order: header -> messages -> input
                                    parentPanel.appendChild(parentHeader);
                                    parentPanel.appendChild(parentMessages);
                                    parentPanel.appendChild(parentInputContainer);
                                    
                                    // Create resize handles for parent panel (AFTER appending to body so they're in DOM)
                                    const resizeHandles = ['nw', 'ne', 'sw', 'se', 'n', 's', 'e', 'w'];
                                    resizeHandles.forEach(direction => {{
                                        const handle = parentDoc.createElement('div');
                                        handle.className = `resize-handle ${{direction}}`;
                                        parentPanel.appendChild(handle);
                                    }});
                                    
                                    console.log('StillMe Chat: Parent panel created with correct HTML structure (header -> messages -> input) + resize handles');
                                    
                                    // Setup event handlers for parent panel (use elements we just created)
                                    closeBtn.onclick = function(e) {{
                                        e.preventDefault();
                                        e.stopPropagation();
                                        const iframes = parentDoc.querySelectorAll('iframe');
                                        for (let iframe of iframes) {{
                                            try {{
                                                if (iframe.contentWindow) {{
                                                    iframe.contentWindow.postMessage({{type: 'stillme_toggle_chat'}}, '*');
                                                }}
                                            }} catch (err) {{
                                                console.warn('StillMe Chat: Could not send toggle message:', err);
                                            }}
                                        }}
                                    }};
                                    
                                    minimizeBtn.onclick = function(e) {{
                                        e.preventDefault();
                                        e.stopPropagation();
                                        parentPanel.classList.toggle('minimized');
                                        if (parentPanel.classList.contains('minimized')) {{
                                            minimizeBtn.textContent = '□';
                                            minimizeBtn.title = 'Restore';
                                        }} else {{
                                            minimizeBtn.textContent = '−';
                                            minimizeBtn.title = 'Minimize';
                                        }}
                                    }};
                                    
                                    fullscreenBtn.onclick = function(e) {{
                                        e.preventDefault();
                                        e.stopPropagation();
                                        parentPanel.classList.toggle('fullscreen');
                                        if (parentPanel.classList.contains('fullscreen')) {{
                                            fullscreenBtn.textContent = '⛶';
                                            fullscreenBtn.title = 'Exit Fullscreen';
                                        }} else {{
                                            fullscreenBtn.textContent = '⛶';
                                            fullscreenBtn.title = 'Toggle Fullscreen';
                                        }}
                                    }};
                                    
                                    // Setup input handler for parent panel (use elements we just created)
                                    // Send message handler
                                    const handleSend = async function() {{
                                        const message = parentInput.value.trim();
                                        if (!message) return;
                                        
                                        // Add user message to parent panel
                                        const userMsg = parentDoc.createElement('div');
                                        userMsg.className = 'stillme-chat-message user';
                                        userMsg.textContent = message;
                                        parentMessages.appendChild(userMsg);
                                        parentMessages.scrollTop = parentMessages.scrollHeight;
                                        
                                        parentInput.value = '';
                                        
                                        // Send to iframe to handle API call
                                        const iframes = parentDoc.querySelectorAll('iframe');
                                        for (let iframe of iframes) {{
                                            try {{
                                                if (iframe.contentWindow) {{
                                                    iframe.contentWindow.postMessage({{
                                                        type: 'stillme_send_message',
                                                        message: message
                                                    }}, '*');
                                                }}
                                            }} catch (err) {{
                                                console.warn('StillMe Chat: Could not send message:', err);
                                            }}
                                        }}
                                    }};
                                    
                                    parentSendBtn.onclick = handleSend;
                                    parentInput.addEventListener('keydown', (e) => {{
                                        if (e.key === 'Enter' && !e.shiftKey) {{
                                            e.preventDefault();
                                            handleSend();
                                        }}
                                    }});
                                    
                                    // Render initial messages in parent panel
                                    if (chatHistory) {{
                                        chatHistory.forEach(msg => {{
                                            const messageDiv = parentDoc.createElement('div');
                                            messageDiv.className = `stillme-chat-message ${{msg.role}}`;
                                            // CRITICAL: Use markdown rendering for assistant messages
                                            if (msg.role === 'assistant') {{
                                                messageDiv.innerHTML = markdownToHtml(msg.content);
                                            }} else {{
                                                messageDiv.textContent = msg.content;
                                            }}
                                            parentMessages.appendChild(messageDiv);
                                        }});
                                        parentMessages.scrollTop = parentMessages.scrollHeight;
                                    }}
                                    
                                    // Setup drag and resize for parent panel
                                    let parentIsDragging = false;
                                    let parentIsResizing = false;
                                    let parentResizeHandle = null;
                                    let parentDragStartX = 0;
                                    let parentDragStartY = 0;
                                    let parentPanelStartX = 0;
                                    let parentPanelStartY = 0;
                                    let parentPanelStartWidth = 0;
                                    let parentPanelStartHeight = 0;
                                    
                                    // Drag functionality for parent panel
                                    parentHeader.addEventListener('mousedown', (e) => {{
                                        if (e.target.closest('.stillme-chat-header-btn, .stillme-chat-close')) return;
                                        if (parentPanel.classList.contains('fullscreen') || parentPanel.classList.contains('minimized')) return;
                                        
                                        parentIsDragging = true;
                                        parentDragStartX = e.clientX;
                                        parentDragStartY = e.clientY;
                                        
                                        const rect = parentPanel.getBoundingClientRect();
                                        parentPanelStartX = rect.left;
                                        parentPanelStartY = rect.top;
                                        
                                        // CRITICAL: Use setProperty with important flag to override CSS
                                        parentPanel.style.setProperty('transform', 'none', 'important');
                                        parentPanel.style.setProperty('left', parentPanelStartX + 'px', 'important');
                                        parentPanel.style.setProperty('top', parentPanelStartY + 'px', 'important');
                                        
                                        e.preventDefault();
                                        e.stopPropagation();
                                    }});
                                    
                                    // Resize functionality for parent panel
                                    function setupParentResizeHandle(handle, direction) {{
                                        if (!handle) {{
                                            console.warn(`StillMe Chat: Parent resize handle not found for direction: ${{direction}}`);
                                            return;
                                        }}
                                        handle.addEventListener('mousedown', (e) => {{
                                            if (parentPanel.classList.contains('fullscreen') || parentPanel.classList.contains('minimized')) return;
                                            
                                            // CRITICAL: Fix scrollbar vs resize handle conflict
                                            // If clicking on right edge (.e handle), check if click is in scrollbar area
                                            if (direction === 'e') {{
                                                const parentMessages = parentDoc.getElementById('stillme-chat-messages');
                                                if (parentMessages) {{
                                                    const messagesRect = parentMessages.getBoundingClientRect();
                                                    const panelRect = parentPanel.getBoundingClientRect();
                                                    // Scrollbar is typically 6-15px wide, check if click is in rightmost 15px (increased from 12px for better detection)
                                                    const clickX = e.clientX;
                                                    const scrollbarAreaStart = panelRect.right - 15; // Rightmost 15px is scrollbar area
                                                    
                                                    if (clickX >= scrollbarAreaStart) {{
                                                        // Click is in scrollbar area, don't start resize - let scrollbar handle it
                                                        console.log('StillMe Chat: Click detected in scrollbar area (parent), skipping resize');
                                                        e.stopPropagation(); // Stop event propagation
                                                        return; // Don't prevent default, let scrollbar work
                                                    }}
                                                }}
                                            }}
                                            
                                            parentIsResizing = true;
                                            parentResizeHandle = direction;
                                            parentDragStartX = e.clientX;
                                            parentDragStartY = e.clientY;
                                            
                                            const rect = parentPanel.getBoundingClientRect();
                                            parentPanelStartWidth = rect.width;
                                            parentPanelStartHeight = rect.height;
                                            
                                            // CRITICAL: getBoundingClientRect() returns visual position (after transform)
                                            // Use this directly as the starting position for resize
                                            // Remove transform first, then set position to maintain visual position
                                            parentPanelStartX = rect.left;
                                            parentPanelStartY = rect.top;
                                            
                                            // CRITICAL: Remove transform and set position simultaneously
                                            // getBoundingClientRect() gives visual position, use it directly
                                            parentPanel.style.setProperty('transform', 'none', 'important');
                                            parentPanel.style.setProperty('left', parentPanelStartX + 'px', 'important');
                                            parentPanel.style.setProperty('top', parentPanelStartY + 'px', 'important');
                                            // Force reflow to ensure styles are applied
                                            parentPanel.offsetHeight;
                                            
                                            console.log(`StillMe Chat: Parent resize started - direction: ${{direction}}, start size: ${{parentPanelStartWidth}}x${{parentPanelStartHeight}}`);
                                            
                                            // CRITICAL: Ensure handle is on top
                                            handle.style.zIndex = '1000001';
                                            handle.style.pointerEvents = 'auto';
                                            
                                            e.preventDefault();
                                            e.stopPropagation();
                                            e.stopImmediatePropagation(); // CRITICAL: Prevent other handlers from interfering
                                        }});
                                    }}
                                    
                                    // Mouse move handler for parent panel drag/resize
                                    // CRITICAL: Attach to parent window, not parent document, to ensure it works
                                    const parentMouseMoveHandler = (e) => {{
                                        // Debug logging
                                        if (parentIsDragging || parentIsResizing) {{
                                            console.log(`StillMe Chat: Mouse move - dragging: ${{parentIsDragging}}, resizing: ${{parentIsResizing}}, handle: ${{parentResizeHandle}}`);
                                        }}
                                        
                                        if (parentIsDragging && !parentPanel.classList.contains('fullscreen') && !parentPanel.classList.contains('minimized')) {{
                                            const deltaX = e.clientX - parentDragStartX;
                                            const deltaY = e.clientY - parentDragStartY;
                                            
                                            let newX = parentPanelStartX + deltaX;
                                            let newY = parentPanelStartY + deltaY;
                                            
                                            const panelWidth = parentPanel.offsetWidth;
                                            const panelHeight = parentPanel.offsetHeight;
                                            newX = Math.max(-panelWidth + 100, Math.min(newX, parentWindow.innerWidth - 100));
                                            newY = Math.max(0, Math.min(newY, parentWindow.innerHeight - 50));
                                            
                                            // CRITICAL: Use setProperty with important flag to override CSS
                                            parentPanel.style.setProperty('left', newX + 'px', 'important');
                                            parentPanel.style.setProperty('top', newY + 'px', 'important');
                                            parentPanel.style.setProperty('transform', 'none', 'important');
                                            
                                            console.log(`StillMe Chat: Dragging panel to: ${{newX}}, ${{newY}}`);
                                        }} else if (parentIsResizing && !parentPanel.classList.contains('fullscreen') && !parentPanel.classList.contains('minimized') && parentResizeHandle) {{
                                            const deltaX = e.clientX - parentDragStartX;
                                            const deltaY = e.clientY - parentDragStartY;
                                            
                                            let newWidth = parentPanelStartWidth;
                                            let newHeight = parentPanelStartHeight;
                                            let newX = parentPanelStartX;
                                            let newY = parentPanelStartY;
                                            
                                            // Reduced min size for better screenshot capability
                                            const PARENT_MIN_WIDTH = 300; // Reduced from 400
                                            const PARENT_MIN_HEIGHT = 300; // Reduced from 400
                                            
                                            if (parentResizeHandle.includes('e')) {{
                                                newWidth = Math.max(PARENT_MIN_WIDTH, parentPanelStartWidth + deltaX);
                                            }}
                                            if (parentResizeHandle.includes('w')) {{
                                                newWidth = Math.max(PARENT_MIN_WIDTH, parentPanelStartWidth - deltaX);
                                                newX = parentPanelStartX + deltaX;
                                            }}
                                            if (parentResizeHandle.includes('s')) {{
                                                newHeight = Math.max(PARENT_MIN_HEIGHT, parentPanelStartHeight + deltaY);
                                            }}
                                            if (parentResizeHandle.includes('n')) {{
                                                newHeight = Math.max(PARENT_MIN_HEIGHT, parentPanelStartHeight - deltaY);
                                                newY = parentPanelStartY + deltaY;
                                            }}
                                            
                                            const maxWidth = parentWindow.innerWidth - newX + 50;
                                            const maxHeight = parentWindow.innerHeight - newY + 50;
                                            newWidth = Math.min(newWidth, maxWidth);
                                            newHeight = Math.min(newHeight, maxHeight);
                                            
                                            // CRITICAL: Use setProperty with important flag to override CSS
                                            parentPanel.style.setProperty('width', newWidth + 'px', 'important');
                                            parentPanel.style.setProperty('height', newHeight + 'px', 'important');
                                            parentPanel.style.setProperty('left', newX + 'px', 'important');
                                            parentPanel.style.setProperty('top', newY + 'px', 'important');
                                            parentPanel.style.setProperty('transform', 'none', 'important');
                                            
                                            console.log(`StillMe Chat: Resizing panel to: ${{newWidth}}x${{newHeight}} at (${{newX}}, ${{newY}})`);
                                        }}
                                    }};
                                    
                                    // CRITICAL: Attach to both document and window to ensure it works
                                    parentDoc.addEventListener('mousemove', parentMouseMoveHandler, true); // Use capture phase
                                    parentWindow.addEventListener('mousemove', parentMouseMoveHandler, true); // Also attach to window
                                    
                                    // Mouse up handler for parent panel
                                    const parentMouseUpHandler = () => {{
                                        if (parentIsDragging || parentIsResizing) {{
                                            console.log(`StillMe Chat: Mouse up - stopping drag/resize`);
                                        }}
                                        parentIsDragging = false;
                                        parentIsResizing = false;
                                        parentResizeHandle = null;
                                    }};
                                    
                                    // CRITICAL: Attach to both document and window to ensure it works
                                    parentDoc.addEventListener('mouseup', parentMouseUpHandler, true); // Use capture phase
                                    parentWindow.addEventListener('mouseup', parentMouseUpHandler, true); // Also attach to window
                                    
                                    if (parentDoc.body) {{
                                        parentDoc.body.appendChild(parentOverlay);
                                        parentDoc.body.appendChild(parentPanel);
                                        console.log('StillMe Chat: Panel and overlay injected into parent window');
                                        
                                        // Setup resize handles AFTER panel is in DOM
                                        setTimeout(() => {{
                                            resizeHandles.forEach(direction => {{
                                                const handle = parentPanel.querySelector(`.resize-handle.${{direction}}`);
                                                if (handle) {{
                                                    setupParentResizeHandle(handle, direction);
                                                    console.log(`StillMe Chat: Parent resize handle ${{direction}} setup complete`);
                                                }} else {{
                                                    console.warn(`StillMe Chat: Parent resize handle ${{direction}} not found!`);
                                                }}
                                            }});
                                            console.log(`StillMe Chat: Parent panel resize handles setup complete (8 handles)`);
                                        }}, 100);
                                    }}
                                }} else {{
                                    parentPanel.style.setProperty('display', 'flex', 'important');
                                    parentOverlay.style.setProperty('display', 'block', 'important');
                                    // Hide iframe panel when parent panel is shown (fix double input issue)
                                    panel.style.setProperty('display', 'none', 'important');
                                    console.log('StillMe Chat: Parent panel shown, iframe panel hidden');
                                }}
                            }} else {{
                                // Close panel - hide in parent, show iframe panel
                                if (parentPanel) {{
                                    parentPanel.style.setProperty('display', 'none', 'important');
                                    parentOverlay.style.setProperty('display', 'none', 'important');
                                    console.log('StillMe Chat: Parent panel hidden');
                                }}
                                // Show iframe panel when parent panel is closed
                                panel.style.setProperty('display', 'flex', 'important');
                            }}
                        }}
                        
                        // Force set display with !important via setProperty (for iframe)
                        if (isVisible) {{
                            // Close panel
                            panel.style.setProperty('display', 'none', 'important');
                            overlay.style.setProperty('display', 'none', 'important');
                            console.log('StillMe Chat: Panel CLOSED (iframe)');
                        }} else {{
                            // Open panel
                            panel.style.setProperty('display', 'flex', 'important');
                            overlay.style.setProperty('display', 'block', 'important');
                            console.log('StillMe Chat: Panel OPENED (iframe)');
                        }}
                        
                        // Verify after setting
                        const panelComputed = window.getComputedStyle(panel).display;
                        const overlayComputed = window.getComputedStyle(overlay).display;
                        console.log('StillMe Chat: Panel computed style after:', panelComputed);
                        console.log('StillMe Chat: Overlay computed style after:', overlayComputed);
                        
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
            
                    // Toggle minimize
                    function toggleMinimize() {{
                        isMinimized = !isMinimized;
                        const minimizeBtn = document.getElementById('minimize-btn');
                        
                        if (isMinimized) {{
                            panel.classList.add('minimized');
                            minimizeBtn.textContent = '□'; // Restore icon
                            minimizeBtn.title = 'Restore';
                            // Exit fullscreen if minimized
                            if (isFullscreen) {{
                                isFullscreen = false;
                                panel.classList.remove('fullscreen');
                                const fullscreenBtn = document.getElementById('fullscreen-btn');
                                fullscreenBtn.textContent = '⛶';
                                fullscreenBtn.title = 'Toggle Fullscreen';
                            }}
                        }} else {{
                            panel.classList.remove('minimized');
                            minimizeBtn.textContent = '−'; // Minimize icon
                            minimizeBtn.title = 'Minimize';
                        }}
                        
                        // Save state
                        savePanelState();
                    }}
                    
                    // Toggle fullscreen
                    function toggleFullscreen() {{
                        // Exit minimize if fullscreen
                        if (isMinimized) {{
                            isMinimized = false;
                            panel.classList.remove('minimized');
                            const minimizeBtn = document.getElementById('minimize-btn');
                            minimizeBtn.textContent = '−';
                            minimizeBtn.title = 'Minimize';
                        }}
                        
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
                        
                        // Save state
                        savePanelState();
                    }}
                    
                    // Drag functionality - improved like Cursor
                    if (header) {{
                        header.addEventListener('mousedown', (e) => {{
                            // Don't drag if clicking on buttons
                            if (e.target.closest('.stillme-chat-header-btn, .stillme-chat-close')) {{
                                return;
                            }}
                            
                            if (isFullscreen || isMinimized) return; // Don't drag in fullscreen or minimized
                            isDragging = true;
                            dragStartX = e.clientX;
                            dragStartY = e.clientY;
                            
                            const rect = panel.getBoundingClientRect();
                            panelStartX = rect.left;
                            panelStartY = rect.top;
                            
                            panel.style.transform = 'none';
                            panel.style.left = panelStartX + 'px';
                            panel.style.top = panelStartY + 'px';
                            
                            // Add dragging class for visual feedback
                            panel.classList.add('dragging');
                            
                            e.preventDefault();
                            e.stopPropagation();
                        }});
                    }}
                    
                    // Resize functionality - improved
                    function setupResizeHandle(handle, direction) {{
                        if (!handle) {{
                            console.warn(`StillMe Chat: Resize handle not found for direction: ${{direction}}`);
                            return;
                        }}
                        handle.addEventListener('mousedown', (e) => {{
                            if (isFullscreen || isMinimized) return; // Don't resize in fullscreen or minimized
                            
                            // CRITICAL: Fix scrollbar vs resize handle conflict
                            // If clicking on right edge (.e handle), check if click is in scrollbar area
                            if (direction === 'e') {{
                                const messagesContainer = document.getElementById('stillme-chat-messages');
                                if (messagesContainer) {{
                                    const messagesRect = messagesContainer.getBoundingClientRect();
                                    const panelRect = panel.getBoundingClientRect();
                                    // Scrollbar is typically 6-15px wide, check if click is in rightmost 15px (increased from 12px for better detection)
                                    const clickX = e.clientX;
                                    const scrollbarAreaStart = panelRect.right - 15; // Rightmost 15px is scrollbar area
                                    
                                    if (clickX >= scrollbarAreaStart) {{
                                        // Click is in scrollbar area, don't start resize - let scrollbar handle it
                                        console.log('StillMe Chat: Click detected in scrollbar area, skipping resize');
                                        e.stopPropagation(); // Stop event propagation
                                        return; // Don't prevent default, let scrollbar work
                                    }}
                                }}
                            }}
                            
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
                            
                            console.log(`StillMe Chat: Resize started - direction: ${{direction}}, start size: ${{panelStartWidth}}x${{panelStartHeight}}`);
                            console.log(`StillMe Chat: Resize handle element:`, handle);
                            console.log(`StillMe Chat: Panel element:`, panel);
                            
                            // CRITICAL: Ensure handle is on top
                            handle.style.zIndex = '1000001';
                            handle.style.pointerEvents = 'auto';
                            
                            e.preventDefault();
                            e.stopPropagation();
                            e.stopImmediatePropagation(); // CRITICAL: Prevent other handlers from interfering
                        }});
                    }}
                    
                    // Setup all resize handles - with error checking and retry
                    function setupAllResizeHandles() {{
                        const resizeHandles = {{
                            nw: document.querySelector('.resize-handle.nw'),
                            ne: document.querySelector('.resize-handle.ne'),
                            sw: document.querySelector('.resize-handle.sw'),
                            se: document.querySelector('.resize-handle.se'),
                            n: document.querySelector('.resize-handle.n'),
                            s: document.querySelector('.resize-handle.s'),
                            e: document.querySelector('.resize-handle.e'),
                            w: document.querySelector('.resize-handle.w')
                        }};
                        
                        let handlesSetup = 0;
                        for (const [direction, handle] of Object.entries(resizeHandles)) {{
                            if (handle) {{
                                setupResizeHandle(handle, direction);
                                handlesSetup++;
                                // Add visual feedback on successful setup
                                handle.style.pointerEvents = 'auto';
                                handle.style.userSelect = 'none';
                            }} else {{
                                console.warn(`StillMe Chat: Resize handle ${{direction}} not found!`);
                            }}
                        }}
                        console.log(`StillMe Chat: Setup ${{handlesSetup}}/8 resize handles`);
                        
                        // If not all handles found, retry after a short delay (DOM might not be ready)
                        if (handlesSetup < 8) {{
                            console.warn(`StillMe Chat: Only ${{handlesSetup}}/8 handles found, retrying...`);
                            setTimeout(setupAllResizeHandles, 100);
                        }}
                    }}
                    
                    // Initial setup
                    setupAllResizeHandles();
                    
                    // CRITICAL: Verify panel layout
                    const messagesEl = document.querySelector('.stillme-chat-messages');
                    const inputEl = document.querySelector('.stillme-chat-input-container');
                    if (messagesEl && inputEl) {{
                        console.log('StillMe Chat: Panel flex-direction:', window.getComputedStyle(panel).flexDirection);
                        console.log('StillMe Chat: Messages order:', window.getComputedStyle(messagesEl).order);
                        console.log('StillMe Chat: Input order:', window.getComputedStyle(inputEl).order);
                        console.log('StillMe Chat: Input margin-top:', window.getComputedStyle(inputEl).marginTop);
                        console.log('StillMe Chat: Messages flex:', window.getComputedStyle(messagesEl).flex);
                        console.log('StillMe Chat: Input flex-grow:', window.getComputedStyle(inputEl).flexGrow);
                    }} else {{
                        console.warn('StillMe Chat: Messages or Input element not found for layout verification');
                    }}
                    
                    // Mouse move handler for drag and resize - improved like Cursor
                    document.addEventListener('mousemove', (e) => {{
                        if (isDragging && !isFullscreen && !isMinimized) {{
                            const deltaX = e.clientX - dragStartX;
                            const deltaY = e.clientY - dragStartY;
                            
                            let newX = panelStartX + deltaX;
                            let newY = panelStartY + deltaY;
                            
                            // Constrain to viewport (allow partial off-screen like Cursor)
                            const panelWidth = panel.offsetWidth;
                            const panelHeight = panel.offsetHeight;
                            newX = Math.max(-panelWidth + 100, Math.min(newX, window.innerWidth - 100));
                            newY = Math.max(0, Math.min(newY, window.innerHeight - 50));
                            
                            panel.style.left = newX + 'px';
                            panel.style.top = newY + 'px';
                            panel.style.transform = 'none'; // CRITICAL: Remove transform when dragging
                        }} else if (isResizing && !isFullscreen && !isMinimized && resizeHandle) {{
                            const deltaX = e.clientX - dragStartX;
                            const deltaY = e.clientY - dragStartY;
                            
                            let newWidth = panelStartWidth;
                            let newHeight = panelStartHeight;
                            let newX = panelStartX;
                            let newY = panelStartY;
                            
                            // Handle different resize directions
                            // Reduced min size for better screenshot capability (can see both input and output)
                            const MIN_WIDTH = 300; // Reduced from 400
                            const MIN_HEIGHT = 300; // Reduced from 400
                            
                            if (resizeHandle.includes('e')) {{
                                newWidth = Math.max(MIN_WIDTH, panelStartWidth + deltaX);
                            }}
                            if (resizeHandle.includes('w')) {{
                                newWidth = Math.max(MIN_WIDTH, panelStartWidth - deltaX);
                                newX = panelStartX + deltaX;
                            }}
                            if (resizeHandle.includes('s')) {{
                                newHeight = Math.max(MIN_HEIGHT, panelStartHeight + deltaY);
                            }}
                            if (resizeHandle.includes('n')) {{
                                newHeight = Math.max(MIN_HEIGHT, panelStartHeight - deltaY);
                                newY = panelStartY + deltaY;
                            }}
                            
                            // Constrain to viewport (allow partial off-screen like Cursor)
                            const maxWidth = window.innerWidth - newX + 50; // Allow 50px off-screen
                            const maxHeight = window.innerHeight - newY + 50; // Allow 50px off-screen
                            newWidth = Math.min(newWidth, maxWidth);
                            newHeight = Math.min(newHeight, maxHeight);
                            
                            panel.style.width = newWidth + 'px';
                            panel.style.height = newHeight + 'px';
                            panel.style.left = newX + 'px';
                            panel.style.top = newY + 'px';
                            panel.style.transform = 'none'; // CRITICAL: Remove transform when resizing
                        }}
                    }});
                    
                    // Mouse up handler
                    document.addEventListener('mouseup', () => {{
                        if (isDragging || isResizing) {{
                            savePanelState();
                            // Remove dragging class
                            panel.classList.remove('dragging');
                        }}
                        isDragging = false;
                        isResizing = false;
                        resizeHandle = null;
                    }});
            
                    // Send message from parent (called via postMessage) - NO CORS issue
                    async function sendMessageFromParent(messageText) {{
                        if (!messageText || !messageText.trim()) return;
                        
                        const message = messageText.trim();
                        
                        // Show processing status immediately (both iframe and parent)
                        const statusDiv = document.getElementById('stillme-chat-status');
                        if (statusDiv) {{
                            statusDiv.textContent = '🤔 StillMe is thinking...';
                            statusDiv.style.display = 'block';
                        }}
                        // Also update parent panel status
                        if (window.parent && window.parent !== window) {{
                            const parentDoc = window.parent.document;
                            const parentStatusDiv = parentDoc.getElementById('stillme-chat-status-parent');
                            if (parentStatusDiv) {{
                                parentStatusDiv.textContent = '🤔 StillMe is thinking...';
                                parentStatusDiv.style.display = 'block';
                            }}
                        }}
                        
                        // Add user message to history
                        chatHistory.push({{ role: 'user', content: message }});
                        renderMessages();
                        
                        // Update parent panel with user message
                        if (window.parent && window.parent !== window) {{
                            const parentDoc = window.parent.document;
                            const parentPanel = parentDoc.getElementById('stillme-chat-panel-parent');
                            if (parentPanel) {{
                                const parentMessages = parentPanel.querySelector('#stillme-chat-messages');
                                if (parentMessages) {{
                                    const userMsg = parentDoc.createElement('div');
                                    userMsg.className = 'stillme-chat-message user';
                                    userMsg.textContent = message;
                                    parentMessages.appendChild(userMsg);
                                    parentMessages.scrollTop = parentMessages.scrollHeight;
                                }}
                            }}
                        }}
                        
                        // Disable send button in iframe
                        const sendBtn = document.getElementById('stillme-chat-send');
                        if (sendBtn) {{
                            sendBtn.disabled = true;
                            sendBtn.textContent = 'Sending...';
                        }}
                        
                        // CRITICAL: Send to backend from iframe context (no CORS issue)
                        try {{
                            // Build conversation history
                            const conversationHistory = [];
                            if (chatHistory.length > 1) {{
                                const historySlice = chatHistory.slice(0, -1).slice(-10);
                                conversationHistory.push(...historySlice);
                            }}
                            
                            const requestPayload = {{
                                message: message,
                                user_id: 'floating_chat_user',
                                use_rag: true,
                                context_limit: 3
                            }};
                            
                            if (conversationHistory.length > 0) {{
                                requestPayload.conversation_history = conversationHistory;
                            }}
                            
                            const response = await fetch(`${{API_BASE}}/api/chat/smart_router`, {{
                                method: 'POST',
                                headers: {{
                                    'Content-Type': 'application/json',
                                }},
                                body: JSON.stringify(requestPayload),
                            }});
                            
                            // Check response status
                            if (!response.ok) {{
                                const errorText = await response.text();
                                let errorMessage = `HTTP ${{response.status}}: ${{response.statusText}}`;
                                try {{
                                    const errorData = JSON.parse(errorText);
                                    errorMessage = errorData.detail || errorData.message || errorMessage;
                                }} catch {{
                                    if (errorText) {{
                                        errorMessage = errorText.substring(0, 200);
                                    }}
                                }}
                                throw new Error(errorMessage);
                            }}
                            
                            const data = await response.json();
                            console.log('StillMe Chat: Received response data:', data);
                            console.log('StillMe Chat: data.response exists?', 'response' in data);
                            console.log('StillMe Chat: data.response value:', data.response ? data.response.substring(0, 100) + '...' : 'NULL/EMPTY');
                            
                            const reply = data.response || data.message || (data.error ? `Error: ${{data.error}}` : JSON.stringify(data));
                            console.log('StillMe Chat: Extracted reply length:', reply ? reply.length : 0);
                            console.log('StillMe Chat: Extracted reply preview:', reply ? reply.substring(0, 100) + '...' : 'EMPTY REPLY');
                            
                            if (!reply || (typeof reply === 'string' && reply.trim() === '')) {{
                                console.error('StillMe Chat: Empty reply received!', data);
                                throw new Error('Empty response from StillMe. Check backend logs.');
                            }}
                            
                            // Display processing steps if available (both iframe and parent)
                            const processingSteps = data.processing_steps || [];
                            if (processingSteps.length > 0) {{
                                const lastSteps = processingSteps.slice(-3).join(' | ');
                                const statusDiv = document.getElementById('stillme-chat-status');
                                if (statusDiv) {{
                                    statusDiv.textContent = lastSteps;
                                    statusDiv.style.display = 'block';
                                }}
                                // Update parent panel status
                                if (window.parent && window.parent !== window) {{
                                    const parentDoc = window.parent.document;
                                    const parentStatusDiv = parentDoc.getElementById('stillme-chat-status-parent');
                                    if (parentStatusDiv) {{
                                        parentStatusDiv.textContent = lastSteps;
                                        parentStatusDiv.style.display = 'block';
                                    }}
                                }}
                            }} else {{
                                const statusDiv = document.getElementById('stillme-chat-status');
                                if (statusDiv) {{
                                    statusDiv.style.display = 'none';
                                }}
                                // Hide parent panel status
                                if (window.parent && window.parent !== window) {{
                                    const parentDoc = window.parent.document;
                                    const parentStatusDiv = parentDoc.getElementById('stillme-chat-status-parent');
                                    if (parentStatusDiv) {{
                                        parentStatusDiv.style.display = 'none';
                                    }}
                                }}
                            }}
                            
                            // Check for learning proposal
                            const learningProposal = data.learning_proposal;
                            const permissionRequest = data.permission_request;
                            if (learningProposal && permissionRequest) {{
                                const statusDiv = document.getElementById('stillme-chat-status');
                                if (statusDiv) {{
                                    statusDiv.textContent = '💡 StillMe wants to learn from this!';
                                    statusDiv.style.display = 'block';
                                    statusDiv.style.color = '#46b3ff';
                                }}
                            }}
                            
                            // Add assistant response
                            console.log('StillMe Chat: Adding reply to chatHistory, length:', reply ? reply.length : 0);
                            chatHistory.push({{ 
                                role: 'assistant', 
                                content: reply,
                                message_id: data.message_id || null,
                                question: message
                            }});
                            console.log('StillMe Chat: chatHistory length after push:', chatHistory.length);
                            renderMessages();
                            console.log('StillMe Chat: renderMessages() called');
                            
                            // Update parent panel with new messages
                            if (window.parent && window.parent !== window) {{
                                const parentDoc = window.parent.document;
                                const parentPanel = parentDoc.getElementById('stillme-chat-panel-parent');
                                if (parentPanel) {{
                                    const parentMessages = parentPanel.querySelector('#stillme-chat-messages');
                                    if (parentMessages) {{
                                        // Clear and re-render all messages
                                        parentMessages.innerHTML = '';
                                        chatHistory.forEach(msg => {{
                                            const messageDiv = parentDoc.createElement('div');
                                            messageDiv.className = `stillme-chat-message ${{msg.role}}`;
                                            // CRITICAL: Use markdown rendering for assistant messages
                                            if (msg.role === 'assistant') {{
                                                messageDiv.innerHTML = markdownToHtml(msg.content);
                                            }} else {{
                                                messageDiv.textContent = msg.content;
                                            }}
                                            parentMessages.appendChild(messageDiv);
                                        }});
                                        parentMessages.scrollTop = parentMessages.scrollHeight;
                                        console.log('StillMe Chat: Updated parent panel with new messages');
                                    }}
                                }}
                            }}
                            
                            // Send message to Streamlit parent
                            window.parent.postMessage({{
                                type: 'stillme_chat_message',
                                history: chatHistory
                            }}, '*');
                            
                        }} catch (error) {{
                            console.error('StillMe Chat Error (from parent):', error);
                            
                            // Show error in status
                            const statusDiv = document.getElementById('stillme-chat-status');
                            if (statusDiv) {{
                                statusDiv.textContent = `❌ Error: ${{error.message}}`;
                                statusDiv.style.display = 'block';
                                statusDiv.style.color = '#ff6b6b';
                            }}
                            
                            // Add error message to chat
                            const errorMessage = error.message || 'Unknown error occurred';
                            chatHistory.push({{ 
                                role: 'assistant', 
                                content: `❌ **Error:** ${{errorMessage}}\n\n💡 Please try again or check backend logs for details.` 
                            }});
                            renderMessages();
                            
                            // Update parent panel with error message
                            if (window.parent && window.parent !== window) {{
                                const parentDoc = window.parent.document;
                                const parentPanel = parentDoc.getElementById('stillme-chat-panel-parent');
                                if (parentPanel) {{
                                    const parentMessages = parentPanel.querySelector('#stillme-chat-messages');
                                    if (parentMessages) {{
                                        // Clear and re-render all messages
                                        parentMessages.innerHTML = '';
                                        chatHistory.forEach(msg => {{
                                            const messageDiv = parentDoc.createElement('div');
                                            messageDiv.className = `stillme-chat-message ${{msg.role}}`;
                                            // CRITICAL: Use markdown rendering for assistant messages
                                            if (msg.role === 'assistant') {{
                                                messageDiv.innerHTML = markdownToHtml(msg.content);
                                            }} else {{
                                                messageDiv.textContent = msg.content;
                                            }}
                                            parentMessages.appendChild(messageDiv);
                                        }});
                                        parentMessages.scrollTop = parentMessages.scrollHeight;
                                    }}
                                }}
                            }}
                        }} finally {{
                            if (sendBtn) {{
                                sendBtn.disabled = false;
                                sendBtn.textContent = 'Send';
                            }}
                        }}
                    }}
                    
                    // Send message (from iframe input)
            async function sendMessage() {{
                const input = document.getElementById('stillme-chat-input');
                const message = input.value.trim();
                
                if (!message) return;
                
                // Disable send button
                const sendBtn = document.getElementById('stillme-chat-send');
                sendBtn.disabled = true;
                sendBtn.textContent = 'Sending...';
                
                // Show processing status immediately (both iframe and parent)
                const statusDiv = document.getElementById('stillme-chat-status');
                if (statusDiv) {{
                    statusDiv.textContent = '🤔 StillMe is thinking...';
                    statusDiv.style.display = 'block';
                }}
                // Also update parent panel status
                if (window.parent && window.parent !== window) {{
                    const parentDoc = window.parent.document;
                    const parentStatusDiv = parentDoc.getElementById('stillme-chat-status-parent');
                    if (parentStatusDiv) {{
                        parentStatusDiv.textContent = '🤔 StillMe is thinking...';
                        parentStatusDiv.style.display = 'block';
                    }}
                }}
                
                // Add user message to history
                chatHistory.push({{ role: 'user', content: message }});
                renderMessages();
                
                // Clear input
                input.value = '';
                
                    // Send to backend
                    try {{
                        // Build conversation history (exclude current message, keep last 5 pairs)
                        // Current message is already in chatHistory, so we exclude it
                        const conversationHistory = [];
                        if (chatHistory.length > 1) {{
                            // Get last 10 messages before current (5 pairs), exclude the last one (current message)
                            const historySlice = chatHistory.slice(0, -1).slice(-10);
                            conversationHistory.push(...historySlice);
                        }}
                        
                        // Build request payload
                        const requestPayload = {{
                            message: message,
                            user_id: 'floating_chat_user',
                            use_rag: true,
                            context_limit: 3
                        }};
                        
                        // Add conversation history if available
                        if (conversationHistory.length > 0) {{
                            requestPayload.conversation_history = conversationHistory;
                        }}
                        
                        const response = await fetch(`${{API_BASE}}/api/chat/smart_router`, {{
                            method: 'POST',
                            headers: {{
                                'Content-Type': 'application/json',
                            }},
                            body: JSON.stringify(requestPayload),
                        }});
                        
                        // Check response status
                        if (!response.ok) {{
                            const errorText = await response.text();
                            let errorMessage = `HTTP ${{response.status}}: ${{response.statusText}}`;
                            try {{
                                const errorData = JSON.parse(errorText);
                                errorMessage = errorData.detail || errorData.message || errorMessage;
                            }} catch {{
                                if (errorText) {{
                                    errorMessage = errorText.substring(0, 200); // Limit error text length
                                }}
                            }}
                            throw new Error(errorMessage);
                        }}
                        
                        const data = await response.json();
                        console.log('StillMe Chat: Received response data:', data);
                        console.log('StillMe Chat: data.response exists?', 'response' in data);
                        console.log('StillMe Chat: data.response value:', data.response ? data.response.substring(0, 100) + '...' : 'NULL/EMPTY');
                        
                        const reply = data.response || data.message || (data.error ? `Error: ${{data.error}}` : JSON.stringify(data));
                        console.log('StillMe Chat: Extracted reply length:', reply ? reply.length : 0);
                        console.log('StillMe Chat: Extracted reply preview:', reply ? reply.substring(0, 100) + '...' : 'EMPTY REPLY');
                        
                        if (!reply || (typeof reply === 'string' && reply.trim() === '')) {{
                            console.error('StillMe Chat: Empty reply received!', data);
                            throw new Error('Empty response from StillMe. Check backend logs.');
                        }}
                        
                        // Display processing steps if available (both iframe and parent)
                        const processingSteps = data.processing_steps || [];
                        if (processingSteps.length > 0) {{
                            console.log('StillMe processing steps:', processingSteps);
                            // Show all steps in status (last 3 steps)
                            const lastSteps = processingSteps.slice(-3).join(' | ');
                            const statusDiv = document.getElementById('stillme-chat-status');
                            if (statusDiv) {{
                                statusDiv.textContent = lastSteps;
                                statusDiv.style.display = 'block';
                            }}
                            // Update parent panel status
                            if (window.parent && window.parent !== window) {{
                                const parentDoc = window.parent.document;
                                const parentStatusDiv = parentDoc.getElementById('stillme-chat-status-parent');
                                if (parentStatusDiv) {{
                                    parentStatusDiv.textContent = lastSteps;
                                    parentStatusDiv.style.display = 'block';
                                }}
                            }}
                        }} else {{
                            // Hide status if no steps (both iframe and parent)
                            const statusDiv = document.getElementById('stillme-chat-status');
                            if (statusDiv) {{
                                statusDiv.style.display = 'none';
                            }}
                            // Hide parent panel status
                            if (window.parent && window.parent !== window) {{
                                const parentDoc = window.parent.document;
                                const parentStatusDiv = parentDoc.getElementById('stillme-chat-status-parent');
                                if (parentStatusDiv) {{
                                    parentStatusDiv.style.display = 'none';
                                }}
                            }}
                        }}
                        
                        // Check for learning proposal
                        const learningProposal = data.learning_proposal;
                        const permissionRequest = data.permission_request;
                        if (learningProposal && permissionRequest) {{
                            console.log('StillMe wants to learn from this conversation!');
                            // Show learning proposal in UI
                            const statusDiv = document.getElementById('stillme-chat-status');
                            if (statusDiv) {{
                                statusDiv.textContent = '💡 StillMe wants to learn from this! Check permission request.';
                                statusDiv.style.display = 'block';
                                statusDiv.style.color = '#46b3ff';
                            }}
                        }}
                        
                        // Add assistant response
                        console.log('StillMe Chat: Adding reply to chatHistory, length:', reply ? reply.length : 0);
                        chatHistory.push({{ 
                            role: 'assistant', 
                            content: reply,
                            message_id: data.message_id || null,
                            question: message
                        }});
                        console.log('StillMe Chat: chatHistory length after push:', chatHistory.length);
                        renderMessages();
                        console.log('StillMe Chat: renderMessages() called');
                            
                            // Update parent panel with new messages
                            if (window.parent && window.parent !== window) {{
                                const parentDoc = window.parent.document;
                                const parentPanel = parentDoc.getElementById('stillme-chat-panel-parent');
                                if (parentPanel) {{
                                    const parentMessages = parentPanel.querySelector('#stillme-chat-messages');
                                    if (parentMessages) {{
                                        // Clear and re-render all messages
                                        parentMessages.innerHTML = '';
                                        chatHistory.forEach(msg => {{
                                            const messageDiv = parentDoc.createElement('div');
                                            messageDiv.className = `stillme-chat-message ${{msg.role}}`;
                                            // CRITICAL: Use markdown rendering for assistant messages
                                            if (msg.role === 'assistant') {{
                                                messageDiv.innerHTML = markdownToHtml(msg.content);
                                            }} else {{
                                                messageDiv.textContent = msg.content;
                                            }}
                                            parentMessages.appendChild(messageDiv);
                                        }});
                                        parentMessages.scrollTop = parentMessages.scrollHeight;
                                        console.log('StillMe Chat: Updated parent panel with new messages');
                                    }}
                                }}
                            }}
                    
                    // Send message to Streamlit parent
                    window.parent.postMessage({{
                        type: 'stillme_chat_message',
                        history: chatHistory
                    }}, '*');
                    
                }} catch (error) {{
                    console.error('StillMe Chat Error:', error);
                    
                    // Show error in status
                    const statusDiv = document.getElementById('stillme-chat-status');
                    if (statusDiv) {{
                        statusDiv.textContent = `❌ Error: ${{error.message}}`;
                        statusDiv.style.display = 'block';
                        statusDiv.style.color = '#ff6b6b';
                    }}
                    
                    // Add error message to chat
                    const errorMessage = error.message || 'Unknown error occurred';
                    chatHistory.push({{ 
                        role: 'assistant', 
                        content: `❌ **Error:** ${{errorMessage}}\n\n💡 Please try again or check backend logs for details.` 
                    }});
                    renderMessages();
                            
                            // Update parent panel with error message
                            if (window.parent && window.parent !== window) {{
                                const parentDoc = window.parent.document;
                                const parentPanel = parentDoc.getElementById('stillme-chat-panel-parent');
                                if (parentPanel) {{
                                    const parentMessages = parentPanel.querySelector('#stillme-chat-messages');
                                    if (parentMessages) {{
                                        // Clear and re-render all messages
                                        parentMessages.innerHTML = '';
                                        chatHistory.forEach(msg => {{
                                            const messageDiv = parentDoc.createElement('div');
                                            messageDiv.className = `stillme-chat-message ${{msg.role}}`;
                                            // CRITICAL: Use markdown rendering for assistant messages
                                            if (msg.role === 'assistant') {{
                                                messageDiv.innerHTML = markdownToHtml(msg.content);
                                            }} else {{
                                                messageDiv.textContent = msg.content;
                                            }}
                                            parentMessages.appendChild(messageDiv);
                                        }});
                                        parentMessages.scrollTop = parentMessages.scrollHeight;
                                    }}
                                }}
                            }}
                }} finally {{
                    sendBtn.disabled = false;
                    sendBtn.textContent = 'Send';
                    input.focus();
                }}
            }}
            
            // Handle Enter key (Enter to send, Shift+Enter for new line)
                    const inputElement = document.getElementById('stillme-chat-input');
                    if (inputElement) {{
                        inputElement.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    sendMessage();
                }}
            }});
                    }}
            
            // Initial render
            renderMessages();
                }} // End of initChat()
                
                // Call initChat when DOM is ready
                if (document.readyState === 'loading') {{
                    document.addEventListener('DOMContentLoaded', initChat);
                }} else {{
                    // DOM already loaded, call immediately
                    initChat();
                }}
                
            }} catch (error) {{
                console.error('StillMe Chat: Fatal error in script:', error);
                console.error('StillMe Chat: Error stack:', error.stack);
            }}
        </script>
    </body>
    </html>
    """
    
    # CRITICAL: Use height=0 to allow full viewport control
    # Note: components.html() doesn't support 'key' parameter
    return components.html(html_content, height=0)

