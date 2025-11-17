"""
Generate Figure 3: Results Comparison Bar Chart
Shows Accuracy and Transparency Score comparison across systems
"""

import matplotlib.pyplot as plt
import numpy as np

# Data from evaluation_summary.json (50-question subset)
systems = ['StillMe', 'Vanilla RAG', 'ChatGPT']
accuracy = [56.00, 54.00, 52.00]
transparency = [70.60, 30.00, 30.00]

# Create figure with two subplots
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

# Set style
plt.style.use('seaborn-v0_8-whitegrid')
colors = ['#2E86AB', '#A23B72', '#F18F01']

# Plot 1: Accuracy
bars1 = ax1.bar(systems, accuracy, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)
ax1.set_ylabel('Accuracy (%)', fontsize=11, fontweight='bold')
ax1.set_title('Accuracy Comparison', fontsize=12, fontweight='bold', pad=10)
ax1.set_ylim(0, 70)
ax1.grid(axis='y', alpha=0.3, linestyle='--')
ax1.set_axisbelow(True)

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars1, accuracy)):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + 1,
             f'{val:.1f}%',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# Plot 2: Transparency Score
bars2 = ax2.bar(systems, transparency, color=colors, alpha=0.8, edgecolor='black', linewidth=1.2)
ax2.set_ylabel('Transparency Score (%)', fontsize=11, fontweight='bold')
ax2.set_title('Transparency Score Comparison', fontsize=12, fontweight='bold', pad=10)
ax2.set_ylim(0, 80)
ax2.grid(axis='y', alpha=0.3, linestyle='--')
ax2.set_axisbelow(True)

# Add value labels on bars
for i, (bar, val) in enumerate(zip(bars2, transparency)):
    height = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2., height + 2,
             f'{val:.1f}%',
             ha='center', va='bottom', fontsize=10, fontweight='bold')

# Adjust layout
plt.tight_layout()

# Save as PDF (preferred for arXiv)
plt.savefig('fig3_results.pdf', dpi=300, bbox_inches='tight', format='pdf')
print("[OK] Generated fig3_results.pdf")

# Also save as PNG (backup)
plt.savefig('fig3_results.png', dpi=300, bbox_inches='tight', format='png')
print("[OK] Generated fig3_results.png")

plt.close()

