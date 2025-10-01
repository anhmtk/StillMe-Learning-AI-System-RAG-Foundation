#!/usr/bin/env python3
"""
Analyze F821 errors to find missing symbols
"""

import json
import re
from collections import Counter

def analyze_f821_errors():
    """Analyze F821 errors from JSON file"""

    with open('f821_errors.json', 'r', encoding='utf-8', errors='replace') as f:
        data = json.load(f)

    symbols = []
    for error in data:
        message = error['message']
        if 'Undefined name' in message:
            # Extract symbol name
            match = re.search(r'`([^`]+)`', message)
            if match:
                symbol = match.group(1)
                symbols.append({
                    'symbol': symbol,
                    'file': error['filename'],
                    'line': error['location']['row'],
                    'message': message
                })

    # Count symbols
    symbol_counts = Counter([s['symbol'] for s in symbols])

    print("Top 20 missing symbols:")
    for symbol, count in symbol_counts.most_common(20):
        print(f"  {symbol}: {count} occurrences")

    print(f"\nTotal F821 errors: {len(symbols)}")
    print(f"Unique symbols: {len(symbol_counts)}")

    # Categorize symbols
    stdlib_symbols = []
    typing_symbols = []
    custom_symbols = []

    for symbol in symbol_counts.keys():
        if symbol in ['List', 'Dict', 'Any', 'Optional', 'Union', 'Tuple', 'Set', 'Callable', 'Type', 'Literal']:
            typing_symbols.append(symbol)
        elif symbol in ['time', 'datetime', 'os', 'sys', 'json', 'pathlib', 'subprocess', 'logging', 'asyncio', 'unittest', 'pytest']:
            stdlib_symbols.append(symbol)
        else:
            custom_symbols.append(symbol)

    print(f"\nTyping symbols: {typing_symbols}")
    print(f"Stdlib symbols: {stdlib_symbols}")
    print(f"Custom symbols: {custom_symbols[:10]}...")  # Show first 10

    return {
        'total_errors': len(symbols),
        'unique_symbols': len(symbol_counts),
        'typing_symbols': typing_symbols,
        'stdlib_symbols': stdlib_symbols,
        'custom_symbols': custom_symbols[:20],
        'top_symbols': dict(symbol_counts.most_common(10))
    }

if __name__ == "__main__":
    result = analyze_f821_errors()
    print(f"\nAnalysis result: {json.dumps(result, indent=2)}")
