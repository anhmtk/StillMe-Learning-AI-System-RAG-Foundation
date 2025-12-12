#!/usr/bin/env python3
"""
Extract CSS and JS from floating_chat.py to separate files for Visual Editor support.
"""
import re
import os

def extract_css_js():
    """Extract CSS and JS from floating_chat.py"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    chat_file = os.path.join(project_root, 'frontend', 'components', 'floating_chat.py')
    static_dir = os.path.join(project_root, 'frontend', 'static')
    
    with open(chat_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract CSS (between <style> and </style>)
    css_match = re.search(r'<style>\s*(.*?)\s*</style>', content, re.DOTALL)
    if not css_match:
        print("[ERROR] Could not find CSS section")
        return
    
    css_content = css_match.group(1)
    # Replace dynamic Python expressions with placeholders (handle both single and double braces)
    css_content = re.sub(r"\{\{'block' if is_open else 'none'\}\}", "{OVERLAY_DISPLAY}", css_content)
    css_content = re.sub(r"\{\{'flex' if is_open else 'none'\}\}", "{PANEL_DISPLAY}", css_content)
    # Also handle cases where it's already in the extracted content
    css_content = re.sub(r"\{'block' if is_open else 'none'\}", "{OVERLAY_DISPLAY}", css_content)
    css_content = re.sub(r"\{'flex' if is_open else 'none'\}", "{PANEL_DISPLAY}", css_content)
    # Remove double braces (Python f-string syntax) - but preserve our placeholders
    css_content = css_content.replace('{{', '{').replace('}}', '}')
    # Restore our placeholders (they got converted)
    css_content = css_content.replace('{OVERLAY_DISPLAY}', '{OVERLAY_DISPLAY}')
    css_content = css_content.replace('{PANEL_DISPLAY}', '{PANEL_DISPLAY}')
    
    # Extract JS (between <script> tags, excluding the first debug script)
    # Find all <script> tags
    script_matches = list(re.finditer(r'<script>(.*?)</script>', content, re.DOTALL))
    if len(script_matches) < 2:
        print("[ERROR] Could not find JS sections")
        return
    
    # Get the main JS (second script tag, which contains the actual logic)
    js_content = script_matches[1].group(1)
    # Replace dynamic Python expressions with placeholders
    js_content = re.sub(r"\{chat_history_json\}", 'CHAT_HISTORY_JSON', js_content)
    js_content = re.sub(r"\{api_base\}", 'API_BASE', js_content)
    js_content = re.sub(r"\{str\(is_open\)\.lower\(\)\}", 'IS_OPEN', js_content)
    # Remove double braces (Python f-string syntax) - but preserve our placeholders
    js_content = js_content.replace('{{', '{').replace('}}', '}')
    # Restore our placeholders (they got converted)
    js_content = js_content.replace('CHAT_HISTORY_JSON', 'CHAT_HISTORY_JSON')
    js_content = js_content.replace('API_BASE', 'API_BASE')
    js_content = js_content.replace('IS_OPEN', 'IS_OPEN')
    
    # Write CSS file
    css_file = os.path.join(static_dir, 'chat_widget.css')
    with open(css_file, 'w', encoding='utf-8') as f:
        f.write(css_content)
    print(f"[OK] Extracted CSS to {css_file}")
    
    # Write JS file
    js_file = os.path.join(static_dir, 'chat_widget.js')
    with open(js_file, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"[OK] Extracted JS to {js_file}")
    
    print("\n[NOTE] Dynamic placeholders:")
    print("  - {OVERLAY_DISPLAY}: Replace with 'block' or 'none' based on is_open")
    print("  - {PANEL_DISPLAY}: Replace with 'flex' or 'none' based on is_open")
    print("  - CHAT_HISTORY_JSON: Replace with actual chat_history JSON")
    print("  - API_BASE: Replace with actual API base URL")

if __name__ == '__main__':
    extract_css_js()

