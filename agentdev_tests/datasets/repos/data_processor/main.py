#!/usr/bin/env python3
"""
Data Processor - Test Repository for AgentDev
Contains performance issues and type errors
"""

import json
import csv
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

class DataProcessor:
    """Data processor with performance and type issues"""
    
    def __init__(self):
        self.data = []
        self.processed_count = 0
    
    def load_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from JSON file - has type annotation issue"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            self.data = data
            return data
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return []
    
    def load_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data from CSV file - has performance issue"""
        data = []
        try:
            with open(file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
            self.data = data
            return data
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return []
        except Exception as e:
            print(f"CSV load error: {e}")
            return []
    
    def process_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process data - has O(n²) performance issue"""
        processed = []
        
        # BUG: Inefficient nested loop - O(n²) complexity
        for i, item in enumerate(data):
            processed_item = item.copy()
            
            # Add processing time (simulating heavy computation)
            time.sleep(0.001)  # BUG: Unnecessary sleep in loop
            
            # Inefficient search for duplicates
            for j, other_item in enumerate(data):
                if i != j and item.get('id') == other_item.get('id'):
                    processed_item['duplicate'] = True
                    break
            
            processed_item['processed_at'] = time.time()
            processed.append(processed_item)
        
        self.processed_count = len(processed)
        return processed
    
    def filter_data(self, data: List[Dict[str, Any]], filter_func) -> List[Dict[str, Any]]:
        """Filter data using a function - has type issue"""
        # BUG: No type checking for filter_func
        return [item for item in data if filter_func(item)]
    
    def aggregate_data(self, data: List[Dict[str, Any]], group_by: str) -> Dict[str, Any]:
        """Aggregate data by field - has KeyError potential"""
        result = {}
        
        for item in data:
            # BUG: No check if group_by key exists
            key = item[group_by]  # Potential KeyError
            if key not in result:
                result[key] = []
            result[key].append(item)
        
        return result
    
    def calculate_statistics(self, data: List[Dict[str, Any]], field: str) -> Dict[str, float]:
        """Calculate statistics for a field - has type conversion issues"""
        values = []
        
        for item in data:
            if field in item:
                # BUG: No type checking, assumes numeric
                value = float(item[field])  # Potential ValueError
                values.append(value)
        
        if not values:
            return {"count": 0, "mean": 0, "min": 0, "max": 0}
        
        return {
            "count": len(values),
            "mean": sum(values) / len(values),
            "min": min(values),
            "max": max(values)
        }
    
    def export_to_json(self, data: List[Dict[str, Any]], file_path: str) -> bool:
        """Export data to JSON file"""
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def export_to_csv(self, data: List[Dict[str, Any]], file_path: str) -> bool:
        """Export data to CSV file - has field handling issue"""
        if not data:
            return False
        
        try:
            with open(file_path, 'w', newline='') as f:
                # BUG: Assumes all items have same keys
                fieldnames = data[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(data)
            return True
        except Exception as e:
            print(f"CSV export error: {e}")
            return False
    
    def get_processed_count(self) -> int:
        """Get count of processed items"""
        return self.processed_count
    
    def clear_data(self):
        """Clear all data"""
        self.data.clear()
        self.processed_count = 0

def main():
    """Main function demonstrating issues"""
    processor = DataProcessor()
    
    # Create sample data
    sample_data = [
        {"id": 1, "name": "Alice", "age": 25, "score": 85.5},
        {"id": 2, "name": "Bob", "age": 30, "score": 92.0},
        {"id": 1, "name": "Alice Duplicate", "age": 25, "score": 85.5},  # Duplicate ID
        {"id": 3, "name": "Charlie", "age": 35, "score": 78.0},
    ]
    
    print("Processing data...")
    
    # This will be slow due to O(n²) complexity
    processed = processor.process_data(sample_data)
    print(f"Processed {len(processed)} items")
    
    # This will cause KeyError if 'department' doesn't exist
    try:
        aggregated = processor.aggregate_data(processed, 'department')
        print(f"Aggregated into {len(aggregated)} groups")
    except KeyError as e:
        print(f"KeyError: {e}")
    
    # This will cause ValueError if 'score' contains non-numeric values
    try:
        stats = processor.calculate_statistics(processed, 'score')
        print(f"Statistics: {stats}")
    except ValueError as e:
        print(f"ValueError: {e}")

if __name__ == "__main__":
    main()
