"""
Generate all figures for StillMe paper
Run this script to create all 3 figures needed for arXiv submission
"""

import subprocess
import sys
import os

# Change to figures directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("Generating all figures for StillMe paper...")
print("=" * 60)
print()

# Check if matplotlib is available
try:
    import matplotlib
    print("[OK] matplotlib found")
except ImportError:
    print("[ERROR] matplotlib not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib"])
    print("[OK] matplotlib installed")

# Generate each figure
scripts = [
    "generate_fig3_results.py",
    "generate_fig1_architecture.py",
    "generate_fig2_validation_chain.py"
]

for script in scripts:
    print(f"\n[INFO] Generating {script}...")
    try:
        subprocess.check_call([sys.executable, script])
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error generating {script}: {e}")
        sys.exit(1)

print()
print("=" * 60)
print("[SUCCESS] All figures generated successfully!")
print("=" * 60)
print()
print("Generated files:")
print("  - fig1_architecture.pdf / .png")
print("  - fig2_validation_chain.pdf / .png")
print("  - fig3_results.pdf / .png")
print()
print("Next steps:")
print("  1. Review the generated figures")
print("  2. If OK, compile LaTeX: cd .. && .\\compile.ps1")
print("  3. Check main.pdf to see figures in context")

