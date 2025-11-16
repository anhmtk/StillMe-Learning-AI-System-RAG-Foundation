"""
Floating Community Panel Component
Creates a resizable, draggable Community panel similar to chat widget
"""

import streamlit.components.v1 as components
import os
import json

def render_floating_community_panel():
    """
    Render a floating Community panel that can be opened/closed
    Similar to floating chat widget but for Community features
    """
    
    # Get API base URL from environment
    api_base = os.getenv("STILLME_API_BASE", "http://localhost:8000")
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            #stillme-community-widget {{
                position: fixed !important;
                z-index: 999998 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                pointer-events: none !important;
            }}
            
            #stillme-community-widget * {{
                pointer-events: auto !important;
            }}
            
            #stillme-community-button {{
                position: fixed !important;
                bottom: 20px !important;
                left: 20px !important;
                width: auto !important;
                height: auto !important;
                padding: 12px 20px !important;
                border-radius: 25px !important;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                border: 3px solid #ffffff !important;
                color: white !important;
                font-size: 14px !important;
                font-weight: bold !important;
                cursor: pointer !important;
                box-shadow: 0 4px 20px rgba(102, 126, 234, 0.6), 0 0 0 4px rgba(102, 126, 234, 0.2) !important;
                transition: all 0.3s ease !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 8px !important;
                z-index: 2147483646 !important;
                visibility: visible !important;
                opacity: 1 !important;
                pointer-events: auto !important;
                margin: 0 !important;
            }}
            
            #stillme-community-button:hover {{
                transform: scale(1.05) !important;
                box-shadow: 0 6px 24px rgba(102, 126, 234, 0.8), 0 0 0 6px rgba(102, 126, 234, 0.3) !important;
            }}
            
            #stillme-community-badge {{
                background: rgba(255, 255, 255, 0.3) !important;
                padding: 2px 8px !important;
                border-radius: 12px !important;
                font-size: 12px !important;
                font-weight: bold !important;
            }}
            
            #stillme-community-overlay {{
                position: fixed !important;
                top: 0 !important;
                left: 0 !important;
                width: 100vw !important;
                height: 100vh !important;
                background: rgba(0, 0, 0, 0.3) !important;
                z-index: 999997 !important;
                display: none !important;
                pointer-events: auto !important;
            }}
            
            #stillme-community-panel {{
                position: fixed !important;
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
                width: 90vw !important;
                max-width: 1200px !important;
                height: 85vh !important;
                max-height: 900px !important;
                background: #1e1e1e !important;
                border-radius: 12px !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(255, 255, 255, 0.1) !important;
                display: none !important;
                flex-direction: column !important;
                border: 1px solid rgba(255, 255, 255, 0.1) !important;
                overflow: hidden !important;
                z-index: 999999 !important;
            }}
            
            #stillme-community-panel.open {{
                display: flex !important;
            }}
            
            .stillme-community-header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                padding: 1rem 1.5rem !important;
                display: flex !important;
                justify-content: space-between !important;
                align-items: center !important;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
                flex-shrink: 0 !important;
            }}
            
            .stillme-community-header h2 {{
                margin: 0 !important;
                color: white !important;
                font-size: 1.5rem !important;
                font-weight: bold !important;
            }}
            
            .stillme-community-close {{
                background: rgba(255, 255, 255, 0.2) !important;
                border: none !important;
                color: white !important;
                width: 32px !important;
                height: 32px !important;
                border-radius: 50% !important;
                cursor: pointer !important;
                font-size: 20px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                transition: all 0.2s ease !important;
            }}
            
            .stillme-community-close:hover {{
                background: rgba(255, 255, 255, 0.3) !important;
                transform: scale(1.1) !important;
            }}
            
            #stillme-community-content {{
                flex: 1 !important;
                overflow-y: auto !important;
                padding: 2rem !important;
                color: #e0e0e0 !important;
            }}
            
            #stillme-community-content::-webkit-scrollbar {{
                width: 8px !important;
            }}
            
            #stillme-community-content::-webkit-scrollbar-track {{
                background: #2a2a2a !important;
            }}
            
            #stillme-community-content::-webkit-scrollbar-thumb {{
                background: #667eea !important;
                border-radius: 4px !important;
            }}
            
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
            }}
            
            .pulse {{
                animation: pulse 2s infinite;
            }}
        </style>
    </head>
    <body>
        <div id="stillme-community-widget">
            <!-- Floating Button -->
            <button id="stillme-community-button" onclick="toggleCommunity()">
                <span>🤝</span>
                <span>Community</span>
                <span id="stillme-community-badge">0</span>
            </button>
            
            <!-- Overlay -->
            <div id="stillme-community-overlay" onclick="closeCommunity()"></div>
            
            <!-- Panel -->
            <div id="stillme-community-panel">
                <div class="stillme-community-header">
                    <h2>🤝 StillMe Community</h2>
                    <button class="stillme-community-close" onclick="closeCommunity()">×</button>
                </div>
                <div id="stillme-community-content">
                    <div id="community-loading" style="text-align: center; padding: 2rem; color: #aaa;">
                        <p>Loading Community...</p>
                    </div>
                    <iframe 
                        id="community-iframe" 
                        src="" 
                        style="width: 100%; height: 100%; border: none; background: #1e1e1e; display: none;"
                        onload="if (typeof iframeLoaded === 'function') iframeLoaded();">
                    </iframe>
                </div>
            </div>
        </div>
        
        <script>
            let isCommunityOpen = false;
            
            function toggleCommunity() {{
                isCommunityOpen = !isCommunityOpen;
                const panel = document.getElementById('stillme-community-panel');
                const overlay = document.getElementById('stillme-community-overlay');
                const iframe = document.getElementById('community-iframe');
                
                if (isCommunityOpen) {{
                    panel.classList.add('open');
                    overlay.style.display = 'block';
                    // Load iframe only when opening
                    if (iframe && !iframe.src) {{
                        iframe.src = window.location.origin + '/Community';
                    }}
                }} else {{
                    panel.classList.remove('open');
                    overlay.style.display = 'none';
                }}
            }}
            
            function iframeLoaded() {{
                const iframe = document.getElementById('community-iframe');
                const loading = document.getElementById('community-loading');
                if (iframe && loading) {{
                    loading.style.display = 'none';
                    iframe.style.display = 'block';
                }}
            }}
            
            function closeCommunity() {{
                isCommunityOpen = false;
                const panel = document.getElementById('stillme-community-panel');
                const overlay = document.getElementById('stillme-community-overlay');
                panel.classList.remove('open');
                overlay.style.display = 'none';
            }}
            
            
            // Fetch daily stats and update badge
            (function() {{
                fetch('{api_base}/api/community/stats')
                    .then(response => {{
                        if (!response.ok) {{
                            throw new Error('Network response was not ok');
                        }}
                        return response.json();
                    }})
                    .then(data => {{
                        const votesNeeded = data.total_votes_needed || 0;
                        const badge = document.getElementById('stillme-community-badge');
                        if (badge) {{
                            if (votesNeeded > 0) {{
                                badge.textContent = votesNeeded;
                                badge.style.background = 'rgba(255, 87, 87, 0.8)';
                                badge.classList.add('pulse');
                            }} else {{
                                badge.textContent = '✓';
                                badge.style.background = 'rgba(76, 179, 255, 0.8)';
                            }}
                        }}
                    }})
                    .catch(error => {{
                        console.error('StillMe Community: Error fetching stats:', error);
                        const badge = document.getElementById('stillme-community-badge');
                        if (badge) {{
                            badge.textContent = '?';
                        }}
                    }});
            }})();
            
            // Close on Escape key
            document.addEventListener('keydown', function(e) {{
                if (e.key === 'Escape' && isCommunityOpen) {{
                    closeCommunity();
                }}
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(html, height=0)

