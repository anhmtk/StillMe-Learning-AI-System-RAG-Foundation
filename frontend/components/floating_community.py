"""
Floating Community Button Component
Displays a floating button to access the Community page
"""

import streamlit.components.v1 as components
import os

def render_floating_community_button():
    """
    Render a floating Community button in the bottom-left corner
    Shows real-time vote count and notification badge
    """
    
    # Get API base URL from environment
    api_base = os.getenv("STILLME_API_BASE", "http://localhost:8000")
    
    html = f"""
    <div id="floating-community-button" style="
        position: fixed !important;
        bottom: 20px !important;
        left: 20px !important;
        z-index: 999999 !important;
        cursor: pointer;
    ">
        <a href="/community.py" target="_blank" style="
            display: flex;
            align-items: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            text-decoration: none;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            font-weight: bold;
            font-size: 14px;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 16px rgba(102, 126, 234, 0.6)';"
           onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(102, 126, 234, 0.4)';">
            <span style="margin-right: 8px; font-size: 18px;">🤝</span>
            <span>Community</span>
            <span id="community-badge" style="
                margin-left: 8px;
                background: rgba(255, 255, 255, 0.3);
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            ">0</span>
        </a>
    </div>
    
    <script>
        // Fetch daily stats and update badge
        (function() {{
            fetch('{api_base}/api/community/stats')
                .then(response => response.json())
                .then(data => {{
                    const votesNeeded = data.total_votes_needed || 0;
                    const badge = document.getElementById('community-badge');
                    if (badge) {{
                        if (votesNeeded > 0) {{
                            badge.textContent = votesNeeded;
                            badge.style.background = 'rgba(255, 87, 87, 0.8)';
                            badge.style.animation = 'pulse 2s infinite';
                        }} else {{
                            badge.textContent = '✓';
                            badge.style.background = 'rgba(76, 179, 255, 0.8)';
                        }}
                    }}
                }})
                .catch(error => {{
                    console.error('Error fetching community stats:', error);
                }});
        }})();
        
        // Add pulse animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulse {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.7; }}
            }}
        `;
        document.head.appendChild(style);
    </script>
    """
    
    components.html(html, height=0)

