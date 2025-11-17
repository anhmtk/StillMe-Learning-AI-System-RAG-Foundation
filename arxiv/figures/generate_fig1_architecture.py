"""
Generate Figure 1: StillMe System Architecture
Shows the flow from External Sources → Learning → RAG → Validation → Response
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, ConnectionPatch

# Create figure
fig, ax = plt.subplots(1, 1, figsize=(10, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

# Define colors
color_source = '#E8F4F8'
color_learning = '#B8E6B8'
color_rag = '#FFE5B4'
color_validation = '#FFB6C1'
color_response = '#DDA0DD'
color_arrow = '#333333'

# Box style
box_style = dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='black', linewidth=1.5)

# 1. External Sources (left)
sources_box = FancyBboxPatch((0.5, 4), 1.8, 1.2, 
                              boxstyle='round,pad=0.3', 
                              facecolor=color_source, 
                              edgecolor='black', linewidth=1.5)
ax.add_patch(sources_box)
ax.text(1.4, 4.9, 'External\nSources', ha='center', va='center', 
        fontsize=10, fontweight='bold', wrap=True)
ax.text(1.4, 4.3, 'RSS, arXiv,\nWikipedia', ha='center', va='center', 
        fontsize=8, style='italic')

# 2. Learning Pipeline (center-left)
learning_box = FancyBboxPatch((2.8, 4), 1.8, 1.2,
                               boxstyle='round,pad=0.3',
                               facecolor=color_learning,
                               edgecolor='black', linewidth=1.5)
ax.add_patch(learning_box)
ax.text(3.7, 4.9, 'Learning\nPipeline', ha='center', va='center',
        fontsize=10, fontweight='bold')
ax.text(3.7, 4.3, 'Every 4 hours', ha='center', va='center',
        fontsize=8, style='italic')

# 3. Vector DB (center)
db_box = FancyBboxPatch((5.1, 4), 1.8, 1.2,
                         boxstyle='round,pad=0.3',
                         facecolor=color_rag,
                         edgecolor='black', linewidth=1.5)
ax.add_patch(db_box)
ax.text(6.0, 4.9, 'Vector\nDatabase', ha='center', va='center',
        fontsize=10, fontweight='bold')
ax.text(6.0, 4.3, 'ChromaDB', ha='center', va='center',
        fontsize=8, style='italic')

# 4. RAG Retrieval (center-right, lower)
rag_box = FancyBboxPatch((5.1, 1.5), 1.8, 1.2,
                          boxstyle='round,pad=0.3',
                          facecolor=color_rag,
                          edgecolor='black', linewidth=1.5)
ax.add_patch(rag_box)
ax.text(6.0, 2.4, 'RAG\nRetrieval', ha='center', va='center',
        fontsize=10, fontweight='bold')
ax.text(6.0, 1.9, 'Semantic Search', ha='center', va='center',
        fontsize=8, style='italic')

# 5. Validation Chain (right, lower)
validation_box = FancyBboxPatch((7.4, 1.5), 1.8, 1.2,
                                boxstyle='round,pad=0.3',
                                facecolor=color_validation,
                                edgecolor='black', linewidth=1.5)
ax.add_patch(validation_box)
ax.text(8.3, 2.4, 'Validation\nChain', ha='center', va='center',
        fontsize=10, fontweight='bold')
ax.text(8.3, 1.9, '6 Validators', ha='center', va='center',
        fontsize=8, style='italic')

# 6. Response (right, top)
response_box = FancyBboxPatch((7.4, 4), 1.8, 1.2,
                              boxstyle='round,pad=0.3',
                              facecolor=color_response,
                              edgecolor='black', linewidth=1.5)
ax.add_patch(response_box)
ax.text(8.3, 4.9, 'Response', ha='center', va='center',
        fontsize=10, fontweight='bold')
ax.text(8.3, 4.3, 'with Citations', ha='center', va='center',
        fontsize=8, style='italic')

# Arrows
# Sources → Learning
arrow1 = FancyArrowPatch((2.3, 4.6), (2.8, 4.6),
                         arrowstyle='->', mutation_scale=20,
                         color=color_arrow, linewidth=2)
ax.add_patch(arrow1)

# Learning → Vector DB
arrow2 = FancyArrowPatch((4.6, 4.6), (5.1, 4.6),
                         arrowstyle='->', mutation_scale=20,
                         color=color_arrow, linewidth=2)
ax.add_patch(arrow2)

# Vector DB → RAG (down)
arrow3 = FancyArrowPatch((6.0, 4.0), (6.0, 2.7),
                         arrowstyle='->', mutation_scale=20,
                         color=color_arrow, linewidth=2)
ax.add_patch(arrow3)

# RAG → Validation
arrow4 = FancyArrowPatch((6.9, 2.1), (7.4, 2.1),
                         arrowstyle='->', mutation_scale=20,
                         color=color_arrow, linewidth=2)
ax.add_patch(arrow4)

# Validation → Response (up)
arrow5 = FancyArrowPatch((8.3, 2.7), (8.3, 4.0),
                         arrowstyle='->', mutation_scale=20,
                         color=color_arrow, linewidth=2)
ax.add_patch(arrow5)

# Title (moved up 0.5cm and doubled font size)
ax.text(5.0, 6.0, 'StillMe System Architecture', ha='center', va='center',
        fontsize=28, fontweight='bold')

# Save
plt.tight_layout()
plt.savefig('fig1_architecture.pdf', dpi=300, bbox_inches='tight', format='pdf')
print("[OK] Generated fig1_architecture.pdf")

plt.savefig('fig1_architecture.png', dpi=300, bbox_inches='tight', format='png')
print("[OK] Generated fig1_architecture.png")

plt.close()

