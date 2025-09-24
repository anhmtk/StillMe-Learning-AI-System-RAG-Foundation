#!/usr/bin/env python3
"""
Generate more test cases for Clarification Core
Creates variations of existing prompts to scale up testing
"""

import csv
import random
import re
from pathlib import Path
from typing import List, Dict, Any

class PromptGenerator:
    """Generate variations of clarification test prompts"""
    
    def __init__(self):
        self.synonyms = {
            "make": ["do", "create", "build", "generate", "produce"],
            "better": ["improve", "enhance", "upgrade", "optimize", "refine"],
            "it": ["this", "that", "the thing", "the item", "the object"],
            "code": ["program", "script", "application", "software", "app"],
            "app": ["application", "program", "software", "system", "platform"],
            "website": ["site", "web page", "web application", "portal", "platform"],
            "function": ["method", "procedure", "routine", "subroutine", "operation"],
            "class": ["object", "entity", "model", "structure", "template"],
            "database": ["db", "data store", "repository", "storage", "warehouse"],
            "analyze": ["examine", "study", "investigate", "review", "assess"],
            "process": ["handle", "manage", "operate", "execute", "run"],
            "fix": ["repair", "correct", "resolve", "solve", "mend"],
            "help": ["assist", "support", "aid", "guide", "facilitate"],
            "write": ["create", "compose", "draft", "author", "develop"],
            "build": ["construct", "assemble", "create", "develop", "make"],
            "design": ["plan", "architect", "structure", "layout", "blueprint"],
            "optimize": ["improve", "enhance", "tune", "refine", "perfect"],
            "faster": ["quicker", "speedier", "swifter", "rapid", "fast"],
            "smaller": ["tinier", "compact", "reduced", "minimal", "lightweight"],
            "bigger": ["larger", "expanded", "increased", "enhanced", "scaled"],
            "cleaner": ["tidier", "neater", "organized", "structured", "refined"],
            "simpler": ["easier", "clearer", "straightforward", "basic", "elementary"],
            "secure": ["safe", "protected", "guarded", "shielded", "defended"],
            "reliable": ["dependable", "stable", "consistent", "trustworthy", "solid"],
            "scalable": ["expandable", "flexible", "adaptable", "growable", "elastic"],
            "maintainable": ["manageable", "supportable", "sustainable", "upkeepable", "serviceable"],
            "testable": ["verifiable", "checkable", "validatable", "provable", "confirmable"],
            "readable": ["understandable", "clear", "comprehensible", "legible", "interpretable"],
            "efficient": ["effective", "productive", "streamlined", "optimized", "performance"],
            "flexible": ["adaptable", "versatile", "configurable", "customizable", "adjustable"],
            "robust": ["strong", "resilient", "durable", "tough", "hardy"],
            "portable": ["mobile", "transferable", "movable", "relocatable", "transportable"],
            "compatible": ["interoperable", "cooperative", "harmonious", "matching", "suitable"],
            "accessible": ["reachable", "available", "approachable", "attainable", "obtainable"],
            "user-friendly": ["intuitive", "easy-to-use", "convenient", "simple", "straightforward"]
        }
        
        self.vague_phrases = [
            "something", "anything", "whatever", "somehow", "somewhere",
            "somewhat", "someway", "sometime", "somewhere", "somehow"
        ]
        
        self.ambiguous_references = [
            "it", "this", "that", "the thing", "the item", "the object",
            "the stuff", "the data", "the file", "the code", "the app"
        ]
        
        self.action_verbs = [
            "make", "do", "create", "build", "write", "fix", "help",
            "improve", "optimize", "enhance", "upgrade", "refine",
            "change", "modify", "update", "adjust", "tune", "configure"
        ]
        
        self.targets = [
            "app", "website", "program", "code", "function", "class",
            "database", "system", "tool", "script", "API", "dashboard"
        ]
    
    def generate_synonym_variations(self, prompt: str) -> List[str]:
        """Generate variations using synonyms"""
        variations = []
        words = prompt.lower().split()
        
        for i, word in enumerate(words):
            if word in self.synonyms:
                for synonym in self.synonyms[word]:
                    new_words = words[:i] + [synonym] + words[i+1:]
                    variations.append(" ".join(new_words))
        
        return variations
    
    def generate_vague_variations(self, prompt: str) -> List[str]:
        """Generate variations with vague phrases"""
        variations = []
        
        # Add vague phrases
        for phrase in self.vague_phrases:
            variations.append(f"{prompt} {phrase}")
            variations.append(f"{phrase} {prompt}")
        
        # Replace specific terms with vague ones
        for word in prompt.split():
            if word.lower() in self.targets:
                for vague in ["something", "anything", "whatever"]:
                    new_prompt = prompt.replace(word, vague)
                    variations.append(new_prompt)
        
        return variations
    
    def generate_ambiguous_reference_variations(self, prompt: str) -> List[str]:
        """Generate variations with ambiguous references"""
        variations = []
        
        for reference in self.ambiguous_references:
            # Replace specific targets with ambiguous references
            for target in self.targets:
                if target in prompt.lower():
                    new_prompt = prompt.replace(target, reference)
                    variations.append(new_prompt)
        
        # Add ambiguous references to the end
        for reference in self.ambiguous_references:
            variations.append(f"{prompt} {reference}")
        
        return variations
    
    def generate_action_variations(self, prompt: str) -> List[str]:
        """Generate variations with different action verbs"""
        variations = []
        
        for action in self.action_verbs:
            # Replace action verbs
            for word in prompt.split():
                if word.lower() in ["make", "do", "create", "build", "write", "fix", "help"]:
                    new_prompt = prompt.replace(word, action)
                    variations.append(new_prompt)
        
        return variations
    
    def generate_goal_variations(self, prompt: str) -> List[str]:
        """Generate variations with different goals"""
        variations = []
        
        goals = [
            "faster", "slower", "smaller", "bigger", "better", "worse",
            "easier", "harder", "cheaper", "more expensive", "more secure",
            "more reliable", "more scalable", "more maintainable", "more testable",
            "more readable", "more efficient", "more flexible", "more robust",
            "more portable", "more compatible", "more accessible", "more user-friendly"
        ]
        
        for goal in goals:
            variations.append(f"Make it {goal}")
            variations.append(f"Do it {goal}")
            variations.append(f"Make this {goal}")
            variations.append(f"Do this {goal}")
        
        return variations
    
    def generate_context_dependency_variations(self, prompt: str) -> List[str]:
        """Generate variations with contextual dependencies"""
        variations = []
        
        dependency_phrases = [
            "like before", "as usual", "the usual way", "like last time",
            "same as before", "like the other one", "similar to that",
            "like that thing", "same as that", "like the previous",
            "as we did", "like we discussed", "as planned",
            "according to plan", "per the spec", "as specified",
            "per requirements", "as required", "per standard",
            "as standard", "per protocol", "as protocol",
            "per procedure", "as procedure"
        ]
        
        for phrase in dependency_phrases:
            variations.append(f"{prompt} {phrase}")
            variations.append(f"{phrase} {prompt}")
        
        return variations
    
    def generate_slang_variations(self, prompt: str) -> List[str]:
        """Generate variations with slang and informal language"""
        variations = []
        
        slang_replacements = {
            "make": "gimme",
            "create": "hook me up with",
            "build": "whip up",
            "write": "crank out",
            "fix": "sort out",
            "help": "lend a hand",
            "improve": "jazz up",
            "optimize": "tune up",
            "enhance": "beef up",
            "upgrade": "level up"
        }
        
        for formal, slang in slang_replacements.items():
            if formal in prompt.lower():
                new_prompt = prompt.replace(formal, slang)
                variations.append(new_prompt)
        
        # Add slang phrases
        slang_phrases = [
            "gimme some", "hook me up", "sort this out", "fix this mess",
            "make it pop", "jazz it up", "spice it up", "beef it up",
            "tweak it", "fiddle with it", "mess around with it",
            "play with it", "toy with it", "fool around with it"
        ]
        
        for phrase in slang_phrases:
            variations.append(phrase)
        
        return variations
    
    def generate_cross_domain_variations(self, prompt: str) -> List[str]:
        """Generate variations with cross-domain actions"""
        variations = []
        
        cross_domain_actions = [
            "analyze", "process", "handle", "manage", "control",
            "monitor", "track", "measure", "calculate", "compute",
            "solve", "resolve", "address", "tackle", "approach",
            "deal with", "work on", "focus on", "concentrate on",
            "emphasize", "highlight", "spotlight", "feature", "showcase", "present"
        ]
        
        for action in cross_domain_actions:
            variations.append(f"{action} this")
            variations.append(f"{action} it")
            variations.append(f"{action} that")
        
        return variations
    
    def generate_all_variations(self, base_prompts: List[str]) -> List[Dict[str, str]]:
        """Generate all variations for a list of base prompts"""
        all_variations = []
        
        for prompt in base_prompts:
            # Generate different types of variations
            synonym_vars = self.generate_synonym_variations(prompt)
            vague_vars = self.generate_vague_variations(prompt)
            ambiguous_vars = self.generate_ambiguous_reference_variations(prompt)
            action_vars = self.generate_action_variations(prompt)
            goal_vars = self.generate_goal_variations(prompt)
            context_vars = self.generate_context_dependency_variations(prompt)
            slang_vars = self.generate_slang_variations(prompt)
            cross_domain_vars = self.generate_cross_domain_variations(prompt)
            
            # Combine all variations
            all_vars = (synonym_vars + vague_vars + ambiguous_vars + 
                       action_vars + goal_vars + context_vars + 
                       slang_vars + cross_domain_vars)
            
            # Remove duplicates and add to results
            unique_vars = list(set(all_vars))
            for var in unique_vars:
                if var != prompt:  # Don't include the original
                    all_variations.append({
                        "prompt": var,
                        "category": "generated_variation",
                        "expected_behavior": "Should ask for clarification"
                    })
        
        return all_variations

def main():
    """Generate additional test cases and append to CSV"""
    generator = PromptGenerator()
    
    # Base prompts to generate variations from
    base_prompts = [
        "Write code for this",
        "Build an app",
        "Do it now",
        "Make it better",
        "Create a function",
        "gimme some code",
        "do the same thing",
        "analyze this",
        "Make it faster",
        "Create a website",
        "Fix this",
        "Help me",
        "Design a system",
        "Process this data",
        "Handle this request"
    ]
    
    # Generate variations
    variations = generator.generate_all_variations(base_prompts)
    
    # Load existing dataset
    dataset_path = Path("datasets/clarification_prompts.csv")
    existing_data = []
    
    if dataset_path.exists():
        with open(dataset_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing_data = list(reader)
    
    # Find next ID
    next_id = len(existing_data) + 1
    
    # Prepare new data
    new_data = []
    for i, variation in enumerate(variations):
        new_data.append({
            "id": str(next_id + i),
            "category": variation["category"],
            "prompt": variation["prompt"],
            "expected_behavior": variation["expected_behavior"]
        })
    
    # Append to CSV
    with open(dataset_path, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['id', 'category', 'prompt', 'expected_behavior']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        for row in new_data:
            writer.writerow(row)
    
    print(f"✅ Generated {len(new_data)} additional test cases")
    print(f"📊 Total test cases: {len(existing_data) + len(new_data)}")
    print(f"📁 Dataset saved to: {dataset_path}")

if __name__ == "__main__":
    main()
