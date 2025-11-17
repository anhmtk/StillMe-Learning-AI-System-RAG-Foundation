"""
Generate Figure 2: Validation Chain Flow
Shows the 6 validators in sequence: Citation → Evidence → Numeric → Confidence → Ethics → Fallback
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(10, 7))
ax.set_xlim(0, 10)
ax.set_ylim(0, 8)
ax.axis('off')

# Define colors
color_validator = '#E8F4F8'
color_pass = '#B8E6B8'
color_fail = '#FFB6C1'
color_arrow = '#333333'

# Box style
box_style = dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='black', linewidth=1.5)

# Title (moved up 0.3cm and doubled font size)
ax.text(5.0, 7.8, 'StillMe Validation Chain', ha='center', va='center',
        fontsize=28, fontweight='bold')

# User Question (top)
user_box = FancyBboxPatch((3.5, 6.2), 3.0, 0.8,
                           boxstyle='round,pad=0.3',
                           facecolor='#FFE5B4',
                           edgecolor='black', linewidth=1.5)
ax.add_patch(user_box)
ax.text(5.0, 6.6, 'User Question', ha='center', va='center',
        fontsize=10, fontweight='bold')

# Arrow down from User Question
arrow_user = FancyArrowPatch((5.0, 6.2), (5.0, 5.8),
                             arrowstyle='->', mutation_scale=20,
                             color=color_arrow, linewidth=2)
ax.add_patch(arrow_user)

# Validators (vertical flow, left side)
validators = [
    ('Citation\nRequired', 2.0, 5.2),
    ('Evidence\nOverlap', 2.0, 4.2),
    ('Numeric\nUnits', 2.0, 3.2),
    ('Confidence\nValidator', 2.0, 2.2),
    ('Ethics\nAdapter', 2.0, 1.2),
]

# Pass/Fail boxes (right side)
pass_fail = [
    ('Pass?', 6.5, 5.2),
    ('Pass?', 6.5, 4.2),
    ('Pass?', 6.5, 3.2),
    ('Pass?', 6.5, 2.2),
    ('Pass?', 6.5, 1.2),
]

# Draw validators and pass/fail boxes
for i, ((val_name, val_x, val_y), (pf_name, pf_x, pf_y)) in enumerate(zip(validators, pass_fail)):
    # Validator box
    val_box = FancyBboxPatch((val_x - 0.8, val_y - 0.4), 1.6, 0.8,
                              boxstyle='round,pad=0.2',
                              facecolor=color_validator,
                              edgecolor='black', linewidth=1.5)
    ax.add_patch(val_box)
    ax.text(val_x, val_y, val_name, ha='center', va='center',
            fontsize=9, fontweight='bold')
    
    # Pass/Fail box
    pf_box = FancyBboxPatch((pf_x - 0.6, pf_y - 0.4), 1.2, 0.8,
                             boxstyle='round,pad=0.2',
                             facecolor=color_pass,
                             edgecolor='black', linewidth=1.5)
    ax.add_patch(pf_box)
    ax.text(pf_x, pf_y, pf_name, ha='center', va='center',
            fontsize=9, fontweight='bold')
    
    # Arrow from validator to pass/fail
    arrow = FancyArrowPatch((val_x + 0.8, val_y), (pf_x - 0.6, pf_y),
                           arrowstyle='->', mutation_scale=15,
                           color=color_arrow, linewidth=1.5)
    ax.add_patch(arrow)
    
    # Arrow down to next validator (except last)
    if i < len(validators) - 1:
        arrow_down = FancyArrowPatch((val_x, val_y - 0.4), (val_x, val_y - 0.8),
                                     arrowstyle='->', mutation_scale=15,
                                     color=color_arrow, linewidth=1.5)
        ax.add_patch(arrow_down)
        
        # Arrow down for pass/fail too
        arrow_down_pf = FancyArrowPatch((pf_x, pf_y - 0.4), (pf_x, pf_y - 0.8),
                                        arrowstyle='->', mutation_scale=15,
                                        color=color_arrow, linewidth=1.5)
        ax.add_patch(arrow_down_pf)

# Final Response (bottom left)
response_box = FancyBboxPatch((0.5, 0.2), 2.0, 0.8,
                              boxstyle='round,pad=0.3',
                              facecolor='#DDA0DD',
                              edgecolor='black', linewidth=1.5)
ax.add_patch(response_box)
ax.text(1.5, 0.6, 'Final Response\n(with Citations)', ha='center', va='center',
        fontsize=9, fontweight='bold')

# Fallback (bottom right)
fallback_box = FancyBboxPatch((7.5, 0.2), 2.0, 0.8,
                               boxstyle='round,pad=0.3',
                               facecolor=color_fail,
                               edgecolor='black', linewidth=1.5)
ax.add_patch(fallback_box)
ax.text(8.5, 0.6, 'Fallback\n(if Critical\nFailure)', ha='center', va='center',
        fontsize=9, fontweight='bold')

# Arrow from last pass/fail to response
arrow_final = FancyArrowPatch((6.5, 0.6), (2.5, 0.6),
                               arrowstyle='->', mutation_scale=20,
                               color=color_arrow, linewidth=2)
ax.add_patch(arrow_final)

# Arrow from last pass/fail to fallback (dashed for failure path)
arrow_fallback = FancyArrowPatch((7.1, 0.6), (7.5, 0.6),
                                 arrowstyle='->', mutation_scale=20,
                                 color='red', linewidth=2, linestyle='--', alpha=0.7)
ax.add_patch(arrow_fallback)

# Save
plt.tight_layout()
plt.savefig('fig2_validation_chain.pdf', dpi=300, bbox_inches='tight', format='pdf')
print("[OK] Generated fig2_validation_chain.pdf")

plt.savefig('fig2_validation_chain.png', dpi=300, bbox_inches='tight', format='png')
print("[OK] Generated fig2_validation_chain.png")

plt.close()

