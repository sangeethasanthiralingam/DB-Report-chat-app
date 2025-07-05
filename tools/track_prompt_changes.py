#!/usr/bin/env python3
"""
Prompt Change Tracker for DB Report Chat App
Helps track and compare prompt changes over time.
"""

import re
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import difflib

class PromptChangeTracker:
    """Track prompt changes in the codebase"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = project_root
        self.prompt_history: List[Dict] = []
        self.changes_file = "prompt_changes.json"
        
    def scan_for_prompts(self) -> Dict[str, List[str]]:
        """Scan the codebase for prompts"""
        prompts = {}
        
        # Common file extensions that might contain prompts
        extensions = ['.py', '.txt', '.md', '.json']
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip common directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv']]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                        # Look for prompt patterns
                        prompt_patterns = [
                            r'You are an expert.*?SQL.*?analyst',
                            r'Generate SQL.*?query',
                            r'Based on the schema',
                            r'Domain.*?context',
                            r'business_terms.*?=',
                            r'prompt.*?=.*?"""',
                            r'f"""SQL.*?analyst',
                        ]
                        
                        found_prompts = []
                        for pattern in prompt_patterns:
                            matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
                            for match in matches:
                                found_prompts.append({
                                    'pattern': pattern,
                                    'match': match.group(),
                                    'line': content[:match.start()].count('\n') + 1
                                })
                        
                        if found_prompts:
                            prompts[file_path] = found_prompts
                            
                    except Exception as e:
                        print(f"Error reading {file_path}: {e}")
        
        return prompts
    
    def extract_prompt_versions(self) -> Dict[str, Dict]:
        """Extract different prompt versions from the codebase"""
        versions = {}
        
        # Look for specific prompt files or sections
        prompt_files = [
            'utils/domain_analyzer.py',
            'utils/database_manager.py',
            'utils/chat_processor.py',
            'business_terms.json'
        ]
        
        for file_path in prompt_files:
            full_path = os.path.join(self.project_root, file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract business terms
                    if file_path.endswith('business_terms.json'):
                        try:
                            business_terms = json.loads(content)
                            versions['business_terms'] = {
                                'file': file_path,
                                'content': business_terms,
                                'type': 'business_terms',
                                'timestamp': datetime.now().isoformat()
                            }
                        except json.JSONDecodeError:
                            pass
                    
                    # Extract SQL generation prompts
                    sql_patterns = [
                        r'def generate_sql.*?prompt.*?=.*?"""(.*?)"""',
                        r'SQL.*?analyst.*?prompt.*?=.*?"""(.*?)"""',
                        r'f"""SQL.*?analyst(.*?)"""',
                    ]
                    
                    for pattern in sql_patterns:
                        matches = re.finditer(pattern, content, re.DOTALL)
                        for i, match in enumerate(matches):
                            prompt_content = match.group(1).strip()
                            if prompt_content:
                                versions[f'sql_generation_{i}'] = {
                                    'file': file_path,
                                    'content': prompt_content,
                                    'type': 'sql_generation',
                                    'timestamp': datetime.now().isoformat()
                                }
                    
                    # Extract domain detection logic
                    domain_patterns = [
                        r'business_terms.*?=.*?{(.*?)}',
                        r'def.*?detect_domain.*?:(.*?)(?=def|\Z)',
                    ]
                    
                    for pattern in domain_patterns:
                        matches = re.finditer(pattern, content, re.DOTALL)
                        for i, match in enumerate(matches):
                            domain_content = match.group(1).strip()
                            if domain_content:
                                versions[f'domain_detection_{i}'] = {
                                    'file': file_path,
                                    'content': domain_content,
                                    'type': 'domain_detection',
                                    'timestamp': datetime.now().isoformat()
                                }
                
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
        
        return versions
    
    def compare_prompts(self, prompt1: str, prompt2: str) -> Dict:
        """Compare two prompts and show differences"""
        comparison = {
            'similarity': 0.0,
            'differences': [],
            'token_count_1': len(prompt1.split()),
            'token_count_2': len(prompt2.split()),
            'length_diff': len(prompt2) - len(prompt1)
        }
        
        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, prompt1, prompt2).ratio()
        comparison['similarity'] = similarity
        
        # Find differences
        diff = difflib.unified_diff(
            prompt1.splitlines(keepends=True),
            prompt2.splitlines(keepends=True),
            lineterm=''
        )
        comparison['differences'] = list(diff)
        
        return comparison
    
    def save_prompt_snapshot(self, version_name: Optional[str] = None):
        """Save current prompt state as a snapshot"""
        if not version_name:
            version_name = f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        snapshot = {
            'version': version_name,
            'timestamp': datetime.now().isoformat(),
            'prompts': self.extract_prompt_versions(),
            'scan_results': self.scan_for_prompts()
        }
        
        self.prompt_history.append(snapshot)
        self.save_history()
        
        print(f"Saved prompt snapshot: {version_name}")
        return snapshot
    
    def load_history(self):
        """Load prompt history from file"""
        try:
            with open(self.changes_file, 'r') as f:
                data = json.load(f)
                self.prompt_history = data.get('history', [])
        except FileNotFoundError:
            self.prompt_history = []
        except Exception as e:
            print(f"Error loading history: {e}")
            self.prompt_history = []
    
    def save_history(self):
        """Save prompt history to file"""
        data = {
            'last_updated': datetime.now().isoformat(),
            'history': self.prompt_history
        }
        
        with open(self.changes_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def generate_change_report(self, version1: Optional[str] = None, version2: Optional[str] = None) -> str:
        """Generate a report of changes between two versions"""
        if not self.prompt_history:
            return "No prompt history available."
        
        if not version1:
            version1 = self.prompt_history[0]['version'] if self.prompt_history else None
        if not version2:
            version2 = self.prompt_history[-1]['version'] if self.prompt_history else None
        
        if not version1 or not version2:
            return "Invalid version specifications."
        
        # Find the versions
        v1_data = next((v for v in self.prompt_history if v['version'] == version1), None)
        v2_data = next((v for v in self.prompt_history if v['version'] == version2), None)
        
        if not v1_data or not v2_data:
            return f"Could not find versions {version1} or {version2}."
        
        report = []
        report.append(f"# Prompt Change Report")
        report.append(f"Comparing {version1} → {version2}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Compare prompts
        v1_prompts = v1_data['prompts']
        v2_prompts = v2_data['prompts']
        
        all_prompt_types = set(v1_prompts.keys()) | set(v2_prompts.keys())
        
        for prompt_type in sorted(all_prompt_types):
            report.append(f"## {prompt_type}")
            
            if prompt_type in v1_prompts and prompt_type in v2_prompts:
                # Both versions exist, compare them
                p1 = v1_prompts[prompt_type]['content']
                p2 = v2_prompts[prompt_type]['content']
                
                if isinstance(p1, dict) and isinstance(p2, dict):
                    # Business terms comparison
                    added = set(p2.keys()) - set(p1.keys())
                    removed = set(p1.keys()) - set(p2.keys())
                    changed = set(p1.keys()) & set(p2.keys())
                    
                    if added:
                        report.append(f"- **Added**: {', '.join(added)}")
                    if removed:
                        report.append(f"- **Removed**: {', '.join(removed)}")
                    if changed:
                        report.append(f"- **Modified**: {', '.join(changed)}")
                else:
                    # String comparison
                    comparison = self.compare_prompts(str(p1), str(p2))
                    report.append(f"- **Similarity**: {comparison['similarity']:.2%}")
                    report.append(f"- **Length change**: {comparison['length_diff']:+d} characters")
                    
                    if comparison['differences']:
                        report.append("- **Key changes**:")
                        for diff in comparison['differences'][:5]:  # Show first 5 differences
                            if diff.startswith('+') or diff.startswith('-'):
                                report.append(f"  {diff.strip()}")
            
            elif prompt_type in v1_prompts:
                report.append("- **Removed** in new version")
            else:
                report.append("- **Added** in new version")
            
            report.append("")
        
        return "\n".join(report)
    
    def list_versions(self) -> List[str]:
        """List all available versions"""
        return [v['version'] for v in self.prompt_history]
    
    def get_version_details(self, version: str) -> Optional[Dict]:
        """Get details of a specific version"""
        return next((v for v in self.prompt_history if v['version'] == version), None)

def main():
    """Example usage of the PromptChangeTracker"""
    tracker = PromptChangeTracker()
    
    # Load existing history
    tracker.load_history()
    
    print("=== Prompt Change Tracker ===")
    print("1. Scan for current prompts")
    print("2. Save current snapshot")
    print("3. List all versions")
    print("4. Generate change report")
    print("5. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            print("\nScanning for prompts...")
            prompts = tracker.scan_for_prompts()
            print(f"Found prompts in {len(prompts)} files:")
            for file_path, prompt_list in prompts.items():
                print(f"  {file_path}: {len(prompt_list)} prompts")
        
        elif choice == '2':
            version_name = input("Enter version name (or press Enter for auto): ").strip()
            if not version_name:
                version_name = None
            snapshot = tracker.save_prompt_snapshot(version_name)
            print(f"Saved snapshot with {len(snapshot['prompts'])} prompt types")
        
        elif choice == '3':
            versions = tracker.list_versions()
            if versions:
                print("\nAvailable versions:")
                for i, version in enumerate(versions, 1):
                    print(f"  {i}. {version}")
            else:
                print("No versions found.")
        
        elif choice == '4':
            versions = tracker.list_versions()
            if len(versions) < 2:
                print("Need at least 2 versions to compare.")
                continue
            
            print("\nAvailable versions:")
            for i, version in enumerate(versions, 1):
                print(f"  {i}. {version}")
            
            try:
                v1_idx = int(input("Enter first version number: ")) - 1
                v2_idx = int(input("Enter second version number: ")) - 1
                
                if 0 <= v1_idx < len(versions) and 0 <= v2_idx < len(versions):
                    report = tracker.generate_change_report(versions[v1_idx], versions[v2_idx])
                    print("\n" + "="*50)
                    print(report)
                    print("="*50)
                else:
                    print("Invalid version numbers.")
            except ValueError:
                print("Please enter valid numbers.")
        
        elif choice == '5':
            print("Goodbye!")
            break
        
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main() 