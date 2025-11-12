"""
Floating Community Button Component
Displays a floating button to access the Community page
"""

import streamlit as st
import os

def render_floating_community_button():
    """
    Render a floating Community button in the bottom-left corner
    Shows real-time vote count and notification badge
    """
    
    # Get API base URL from environment
    api_base = os.getenv("STILLME_API_BASE", "http://localhost:8000")
    
    # Use st.markdown with unsafe_allow_html for better compatibility
    html = f"""
    <style>
        #floating-community-button {{
            position: fixed !important;
            bottom: 20px !important;
            left: 20px !important;
            z-index: 999999 !important;
            cursor: pointer;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        
        #floating-community-button a {{
            display: flex !important;
            align-items: center !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            color: white !important;
            padding: 12px 20px !important;
            border-radius: 25px !important;
            text-decoration: none !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
            transition: all 0.3s ease !important;
            font-weight: bold !important;
            font-size: 14px !important;
            border: none !important;
        }}
        
        #floating-community-button a:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.6) !important;
        }}
        
        #community-badge {{
            margin-left: 8px !important;
            background: rgba(255, 255, 255, 0.3) !important;
            padding: 2px 8px !important;
            border-radius: 12px !important;
            font-size: 12px !important;
            font-weight: bold !important;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.7; }}
        }}
        
        .pulse {{
            animation: pulse 2s infinite;
        }}
    </style>
    
    <div id="floating-community-button">
        <a href="/community.py" target="_blank">
            <span style="margin-right: 8px; font-size: 18px;">🤝</span>
            <span>Community</span>
            <span id="community-badge">0</span>
        </a>
    </div>
    
    <script>
        (function() {{
            console.log('StillMe Community: Initializing floating button...');
            
            // Ensure button is visible
            const button = document.getElementById('floating-community-button');
            if (button) {{
                button.style.display = 'block';
                button.style.visibility = 'visible';
                console.log('StillMe Community: Button element found and made visible');
            }} else {{
                console.error('StillMe Community: Button element not found!');
            }}
            
            // Fetch daily stats and update badge
            fetch('{api_base}/api/community/stats')
                .then(response => {{
                    if (!response.ok) {{
                        throw new Error('Network response was not ok');
                    }}
                    return response.json();
                }})
                .then(data => {{
                    console.log('StillMe Community: Stats received', data);
                    const votesNeeded = data.total_votes_needed || 0;
                    const badge = document.getElementById('community-badge');
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
                    // Show button even if API fails
                    const badge = document.getElementById('community-badge');
                    if (badge) {{
                        badge.textContent = '?';
                    }}
                }});
        }})();
    </script>
    """
    
    st.markdown(html, unsafe_allow_html=True)

