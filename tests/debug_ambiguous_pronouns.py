#!/usr/bin/env python3

from stillme_core.modules.clarification_handler import ClarificationHandler

def debug_ambiguous_pronouns():
    h = ClarificationHandler()
    inputs = [
        'Make this better',
        'Update those files', 
        'Delete them',
        'Move it over there',
        'Change this to that',
        'Replace it with something else'
    ]
    
    for text in inputs:
        r = h.detect_ambiguity(text)
        print(f'{text}: needs_clarification={r.needs_clarification}, confidence={r.confidence}')

if __name__ == "__main__":
    debug_ambiguous_pronouns()
