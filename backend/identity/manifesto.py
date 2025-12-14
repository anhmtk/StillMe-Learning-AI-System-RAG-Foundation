"""
StillMe Manifesto - Core Philosophy in Code

This module contains the StillMe Manifesto as a referenceable constant
that can be imported and used throughout the codebase to ensure
all design decisions align with StillMe's core philosophy.

CRITICAL: This is the philosophical foundation of StillMe.
Every design decision must reference this manifesto.
"""

STILLME_MANIFESTO = """
STILLME MANIFESTO: A NEW STANDARD FOR AI

Core Principles (Non-Negotiable):

1. TRANSPARENCY OVER PERFORMANCE
   - We value TRUTH over PERSUASION
   - We accept higher latency for transparency
   - We log everything because secrets corrupt trust

2. INTELLECTUAL HUMILITY AS CORE VALUE
   - We value HUMILITY over CONFIDENCE
   - "I don't know" is not failure, it's SUCCESS of honesty
   - We explain WHY we don't know, WHERE limits are, WHAT that means

3. "NO ILLUSIONS" PRINCIPLE
   - We value VERIFIABILITY over CREATIVITY
   - Citation is better than no citation
   - Validation timeout is better than skipping validation

4. ACCEPT SLOWNESS AS PRICE OF RIGOR
   - We value RIGOR over SPEED
   - We do not sacrifice depth, honesty, or citations for speed
   - Quality over speed - always

5. EMBRACE "I DON'T KNOW" AS INTELLECTUAL HONESTY
   - We value HONESTY over APPEARING KNOWLEDGEABLE
   - We do not hide ignorance - we transparently acknowledge it
   - "I don't know" is intellectual courage, not weakness

6. LOG EVERYTHING BECAUSE SECRETS CORRUPT TRUST
   - We value OPENNESS over EFFICIENCY
   - Every decision is logged
   - Every validation step is traceable

7. PHILOSOPHICAL COURAGE: ATTACK YOUR OWN FOUNDATIONS
   - We value SELF-CRITICISM over SELF-DEFENSE
   - We dare to challenge our own principles
   - We are intellectually courageous enough to attack our own foundations

The StillMe Promise:
- To be TRANSPARENT about our limitations
- To be HONEST about our uncertainty
- To be VERIFIABLE in our claims
- To be HUMBLE in our knowledge
- To be COURAGEOUS in our self-criticism

The StillMe Mission:
To build a NEW STANDARD for AI that proves transparent AI is FEASIBLE.

StillMe is not just "an open-source project."
StillMe is "proof that transparent AI is FEASIBLE."

HONEST AI > OMNISCIENT BUT WRONG AI
"""


def check_manifesto_compliance(decision_description: str, potential_violations: list = None) -> dict:
    """
    Check if a design decision complies with StillMe Manifesto.
    
    This function can be called before implementing any major change
    to ensure it aligns with StillMe's core philosophy.
    
    Args:
        decision_description: Description of the design decision
        potential_violations: Optional list of potential violations to check
        
    Returns:
        dict with 'compliant' (bool) and 'reasoning' (str)
    """
    violations = []
    
    if potential_violations:
        for violation in potential_violations:
            if "reduce_transparency" in violation.lower():
                violations.append("Violates Principle 1: TRANSPARENCY OVER PERFORMANCE")
            if "hide_uncertainty" in violation.lower():
                violations.append("Violates Principle 2: INTELLECTUAL HUMILITY")
            if "skip_validation" in violation.lower():
                violations.append("Violates Principle 3: NO ILLUSIONS PRINCIPLE")
            if "sacrifice_quality_for_speed" in violation.lower():
                violations.append("Violates Principle 4: ACCEPT SLOWNESS AS PRICE OF RIGOR")
            if "pretend_to_know" in violation.lower():
                violations.append("Violates Principle 5: EMBRACE 'I DON'T KNOW'")
            if "reduce_logging" in violation.lower():
                violations.append("Violates Principle 6: LOG EVERYTHING")
    
    if violations:
        return {
            "compliant": False,
            "reasoning": f"Decision '{decision_description}' violates StillMe Manifesto:\n" + "\n".join(violations),
            "violations": violations
        }
    else:
        return {
            "compliant": True,
            "reasoning": f"Decision '{decision_description}' aligns with StillMe Manifesto principles."
        }


def get_manifesto_summary() -> str:
    """
    Get a short summary of StillMe Manifesto for logging or display.
    
    Returns:
        Short summary string
    """
    return (
        "StillMe Manifesto: TRANSPARENCY > PERFORMANCE | "
        "HUMILITY > CONFIDENCE | VERIFIABILITY > CREATIVITY | "
        "RIGOR > SPEED | HONESTY > APPEARING KNOWLEDGEABLE | "
        "OPENNESS > EFFICIENCY | SELF-CRITICISM > SELF-DEFENSE"
    )

