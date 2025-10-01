#!/usr/bin/env python3
"""
PHA 1 - Thu thập bằng chứng cho F821 symbols
"""

import json
import re
from collections import defaultdict
from pathlib import Path

def get_f821_evidence():
    """Thu thập bằng chứng cho F821 symbols"""
    
    # Sử dụng AgentDev để scan
    from agent_dev.core.agentdev import AgentDev
    agentdev = AgentDev()
    errors = agentdev.scan_errors()
    f821_errors = [e for e in errors if e.rule == 'F821']
    
    # Nhóm theo symbol
    symbol_evidence = defaultdict(list)
    
    for error in f821_errors:
        if '`' in error.msg:
            parts = error.msg.split('`')
            if len(parts) >= 2:
                symbol = parts[1]
                symbol_evidence[symbol].append({
                    'file': error.file,
                    'line': error.line,
                    'message': error.msg
                })
    
    # Phân tích từng symbol
    symbols_analysis = []
    
    for symbol, usages in symbol_evidence.items():
        # Thu thập context cho mỗi usage
        usages_with_context = []
        
        for usage in usages:
            file_path = usage['file']
            line_num = usage['line']
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                
                # Lấy 3 dòng context
                start_line = max(0, line_num - 2)
                end_line = min(len(lines), line_num + 1)
                context_lines = []
                
                for i in range(start_line, end_line):
                    line_content = lines[i].rstrip()
                    prefix = "+" if i == line_num - 1 else "-"
                    context_lines.append(f"{prefix}{i+1}:{line_content}")
                
                usages_with_context.append({
                    'file': file_path,
                    'line': line_num,
                    'context': context_lines
                })
                
            except Exception as e:
                usages_with_context.append({
                    'file': file_path,
                    'line': line_num,
                    'context': [f"Error reading file: {e}"]
                })
        
        # Suy luận kind dựa trên context
        inferred_kind, required_members, confidence = infer_symbol_kind(symbol, usages_with_context)
        
        # Tìm preferred module
        preferred_module = find_preferred_module(symbol, usages_with_context)
        
        symbols_analysis.append({
            'name': symbol,
            'usages': usages_with_context,
            'inferred_kind': inferred_kind,
            'required_members_or_fields': required_members,
            'preferred_module': preferred_module,
            'confidence': confidence
        })
    
    # Sắp xếp theo confidence giảm dần
    symbols_analysis.sort(key=lambda x: x['confidence'], reverse=True)
    
    return {
        'symbols': symbols_analysis,
        'total_candidates': len(symbols_analysis)
    }

def infer_symbol_kind(symbol, usages):
    """Suy luận loại symbol dựa trên usage patterns"""
    
    all_context = []
    for usage in usages:
        all_context.extend(usage['context'])
    
    context_text = '\n'.join(all_context)
    
    # Enum patterns
    enum_patterns = [
        rf'{symbol}\.(\w+)',  # Symbol.MEMBER
        rf'\.{symbol}\.(\w+)',  # .Symbol.MEMBER
        rf'{symbol}\.value',  # Symbol.value
        rf'{symbol}\.name',   # Symbol.name
    ]
    
    # Class patterns
    class_patterns = [
        rf'{symbol}\(',  # Symbol()
        rf'{symbol}\.\w+\(',  # Symbol.method()
        rf': {symbol}',  # type hint
        rf'-> {symbol}',  # return type
    ]
    
    # Literal/Const patterns
    literal_patterns = [
        rf'== {symbol}',  # == Symbol
        rf'!= {symbol}',  # != Symbol
        rf'is {symbol}',  # is Symbol
        rf'"{symbol}"',   # "Symbol"
        rf"'{symbol}'",   # 'Symbol'
    ]
    
    # Đếm patterns
    enum_count = sum(len(re.findall(pattern, context_text)) for pattern in enum_patterns)
    class_count = sum(len(re.findall(pattern, context_text)) for pattern in class_patterns)
    literal_count = sum(len(re.findall(pattern, context_text)) for pattern in literal_patterns)
    
    # Suy luận kind
    if enum_count > 0:
        # Extract enum members
        members = set()
        for pattern in enum_patterns[:2]:  # Symbol.MEMBER patterns
            matches = re.findall(pattern, context_text)
            members.update(matches)
        
        confidence = min(0.9, 0.5 + (enum_count * 0.1))
        return 'Enum', list(members), confidence
    
    elif class_count > 0:
        confidence = min(0.8, 0.4 + (class_count * 0.1))
        return 'Class', [], confidence
    
    elif literal_count > 0:
        confidence = min(0.7, 0.3 + (literal_count * 0.1))
        return 'Literal', [symbol], confidence
    
    else:
        # Default based on symbol name patterns
        if symbol.isupper():
            return 'Const', [symbol], 0.3
        elif symbol[0].isupper():
            return 'Class', [], 0.2
        else:
            return 'Unknown', [], 0.1

def find_preferred_module(symbol, usages):
    """Tìm module ưu tiên dựa trên usage patterns"""
    
    # Common patterns
    if symbol in ['JobStatus', 'HealthStatus', 'RiskLevel']:
        return 'stillme_core.core.status'
    elif symbol in ['Mock', 'patch', 'AsyncMock']:
        return 'unittest.mock'
    elif symbol in ['Any', 'Dict', 'List', 'Optional', 'Union']:
        return 'typing'
    elif symbol in ['PIIType', 'PrivacyLevel']:
        return 'stillme_core.privacy.privacy_manager'
    elif symbol in ['given', 'settings']:
        return 'hypothesis'
    else:
        return f'stillme_core.core.{symbol.lower()}'

if __name__ == "__main__":
    result = get_f821_evidence()
    print(json.dumps(result, indent=2))
