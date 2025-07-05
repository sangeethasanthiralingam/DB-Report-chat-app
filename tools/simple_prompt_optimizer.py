#!/usr/bin/env python3
"""
Simple Prompt Optimizer for DB Report Chat App
Helps analyze and optimize prompts without external dependencies.
"""

import json
import time
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@dataclass
class PromptMetrics:
    """Metrics for prompt performance"""
    version: str
    word_count: int
    character_count: int
    accuracy: float
    response_time: float
    error_rate: float
    date: datetime
    
    def to_dict(self) -> Dict:
        return {
            'version': self.version,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'accuracy': self.accuracy,
            'response_time': self.response_time,
            'error_rate': self.error_rate,
            'date': self.date.isoformat()
        }

class SimplePromptOptimizer:
    """Simple tool for analyzing and optimizing prompts"""
    
    def __init__(self):
        self.metrics_history: List[PromptMetrics] = []
        
    def analyze_prompt(self, prompt: str, prompt_type: str = "sql_generation") -> Dict:
        """Analyze a prompt for optimization opportunities"""
        word_count = len(prompt.split())
        char_count = len(prompt)
        
        analysis = {
            'prompt_type': prompt_type,
            'word_count': word_count,
            'character_count': char_count,
            'estimated_tokens': word_count * 1.3,  # Rough estimate
            'optimization_suggestions': []
        }
        
        # Size optimization suggestions
        if word_count > 200:
            analysis['optimization_suggestions'].append({
                'type': 'high_word_count',
                'severity': 'high',
                'suggestion': 'Consider using compact schema formatting or domain-specific context'
            })
        
        # Check for redundant phrases
        redundant_phrases = [
            "You are an expert",
            "Please generate",
            "Based on the",
            "Using the schema",
            "Please ensure",
            "Make sure to"
        ]
        
        for phrase in redundant_phrases:
            if phrase.lower() in prompt.lower():
                analysis['optimization_suggestions'].append({
                    'type': 'redundant_phrase',
                    'severity': 'medium',
                    'suggestion': f'Consider removing or shortening: "{phrase}"'
                })
        
        # Check for verbose schema descriptions
        if 'CREATE TABLE' in prompt or 'CREATE DATABASE' in prompt:
            analysis['optimization_suggestions'].append({
                'type': 'verbose_schema',
                'severity': 'high',
                'suggestion': 'Use compact schema format instead of full CREATE statements'
            })
        
        # Check for repetitive instructions
        instruction_count = prompt.lower().count('please') + prompt.lower().count('ensure') + prompt.lower().count('make sure')
        if instruction_count > 3:
            analysis['optimization_suggestions'].append({
                'type': 'repetitive_instructions',
                'severity': 'medium',
                'suggestion': 'Reduce repetitive instructions - be more concise'
            })
        
        return analysis
    
    def optimize_prompt(self, original_prompt: str, target_words: int = 100) -> Tuple[str, Dict]:
        """Optimize a prompt to reduce word count"""
        original_words = len(original_prompt.split())
        optimized_prompt = original_prompt
        
        optimizations = {
            'original_words': original_words,
            'target_words': target_words,
            'applied_optimizations': []
        }
        
        # Remove redundant phrases
        redundant_removals = [
            ("You are an expert SQL analyst.", "SQL analyst:"),
            ("Please generate a SQL query.", "Generate SQL:"),
            ("Based on the schema above,", ""),
            ("Using the provided schema,", ""),
            ("Please ensure the query is optimized.", ""),
            ("Make sure to follow best practices.", ""),
            ("Please make sure to", ""),
            ("Please ensure that", ""),
        ]
        
        for old_phrase, new_phrase in redundant_removals:
            if old_phrase in optimized_prompt:
                optimized_prompt = optimized_prompt.replace(old_phrase, new_phrase)
                optimizations['applied_optimizations'].append(f'Replaced "{old_phrase}" with "{new_phrase}"')
        
        # Remove extra whitespace and newlines
        optimized_prompt = ' '.join(optimized_prompt.split())
        
        # Truncate if still too long
        current_words = len(optimized_prompt.split())
        if current_words > target_words:
            # Simple truncation (in practice, you'd want smarter truncation)
            words = optimized_prompt.split()
            while current_words > target_words and words:
                words.pop()
                optimized_prompt = ' '.join(words)
                current_words = len(optimized_prompt.split())
            
            optimizations['applied_optimizations'].append(f'Truncated to {target_words} words')
        
        optimizations['final_words'] = len(optimized_prompt.split())
        optimizations['word_reduction'] = original_words - optimizations['final_words']
        optimizations['reduction_percentage'] = (optimizations['word_reduction'] / original_words) * 100
        
        return optimized_prompt, optimizations
    
    def create_compact_schema_format(self, schema: Dict) -> str:
        """Create a compact schema format to reduce size"""
        compact_parts = []
        
        for table_name, table_info in schema.get('tables', {}).items():
            columns = []
            for col_name, col_info in table_info.get('columns', {}).items():
                col_type = col_info.get('type', 'unknown')
                nullable = '' if col_info.get('nullable', True) else ' NOT NULL'
                columns.append(f"{col_name}:{col_type}{nullable}")
            
            compact_parts.append(f"{table_name}({', '.join(columns)})")
        
        return " | ".join(compact_parts)
    
    def generate_domain_specific_prompt(self, domain: str, question: str, schema: Dict) -> str:
        """Generate a domain-specific optimized prompt"""
        compact_schema = self.create_compact_schema_format(schema)
        
        # Domain-specific context
        domain_contexts = {
            'hr': 'HR system with employees, departments, attendance',
            'inventory': 'Inventory system with products, stock, suppliers',
            'financial': 'Financial system with accounts, transactions, payments',
            'ecommerce': 'E-commerce system with orders, customers, products'
        }
        
        domain_context = domain_contexts.get(domain.lower(), f'{domain} system')
        
        prompt = f"""SQL analyst for {domain_context}
Schema: {compact_schema}
Q: {question}
SQL:"""
        
        return prompt
    
    def benchmark_prompt(self, prompt: str, test_questions: List[str], 
                        execute_func=None) -> PromptMetrics:
        """Benchmark a prompt against test questions"""
        start_time = time.time()
        success_count = 0
        error_count = 0
        
        for question in test_questions:
            try:
                # This would be your actual SQL generation call
                if execute_func:
                    result = execute_func(prompt, question)
                    if result and not result.get('error'):
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    # Mock execution for testing
                    success_count += 1
            except Exception as e:
                error_count += 1
                logging.warning(f"Error processing question: {e}")
        
        total_questions = len(test_questions)
        accuracy = success_count / total_questions if total_questions > 0 else 0
        error_rate = error_count / total_questions if total_questions > 0 else 0
        response_time = time.time() - start_time
        
        metrics = PromptMetrics(
            version=f"v{len(self.metrics_history) + 1}.0",
            word_count=len(prompt.split()),
            character_count=len(prompt),
            accuracy=accuracy,
            response_time=response_time,
            error_rate=error_rate,
            date=datetime.now()
        )
        
        self.metrics_history.append(metrics)
        return metrics
    
    def compare_prompts(self, prompt1: str, prompt2: str, 
                       test_questions: List[str]) -> Dict:
        """Compare two prompts"""
        metrics1 = self.benchmark_prompt(prompt1, test_questions)
        metrics2 = self.benchmark_prompt(prompt2, test_questions)
        
        comparison = {
            'prompt1': {
                'metrics': metrics1.to_dict(),
                'analysis': self.analyze_prompt(prompt1)
            },
            'prompt2': {
                'metrics': metrics2.to_dict(),
                'analysis': self.analyze_prompt(prompt2)
            },
            'improvements': {
                'word_reduction': metrics1.word_count - metrics2.word_count,
                'accuracy_improvement': metrics2.accuracy - metrics1.accuracy,
                'speed_improvement': metrics1.response_time - metrics2.response_time,
                'error_reduction': metrics1.error_rate - metrics2.error_rate
            }
        }
        
        return comparison
    
    def generate_optimization_report(self) -> str:
        """Generate a comprehensive optimization report"""
        if not self.metrics_history:
            return "No metrics available for report generation."
        
        report = []
        report.append("# Simple Prompt Optimization Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary statistics
        total_prompts = len(self.metrics_history)
        avg_words = sum(m.word_count for m in self.metrics_history) / total_prompts
        avg_accuracy = sum(m.accuracy for m in self.metrics_history) / total_prompts
        
        report.append("## Summary Statistics")
        report.append(f"- Total prompts analyzed: {total_prompts}")
        report.append(f"- Average words: {avg_words:.1f}")
        report.append(f"- Average accuracy: {avg_accuracy:.2%}")
        report.append("")
        
        # Performance trends
        report.append("## Performance Trends")
        for i, metrics in enumerate(self.metrics_history):
            report.append(f"### {metrics.version}")
            report.append(f"- Words: {metrics.word_count}")
            report.append(f"- Characters: {metrics.character_count}")
            report.append(f"- Accuracy: {metrics.accuracy:.2%}")
            report.append(f"- Response time: {metrics.response_time:.3f}s")
            report.append(f"- Error rate: {metrics.error_rate:.2%}")
            report.append("")
        
        # Recommendations
        report.append("## Optimization Recommendations")
        
        latest_metrics = self.metrics_history[-1]
        if latest_metrics.word_count > 150:
            report.append("- **High word count**: Consider implementing compact schema formatting")
        
        if latest_metrics.accuracy < 0.8:
            report.append("- **Low accuracy**: Consider adding domain-specific context")
        
        if latest_metrics.error_rate > 0.2:
            report.append("- **High error rate**: Consider implementing error recovery mechanisms")
        
        return "\n".join(report)
    
    def save_metrics(self, filename: str = "simple_prompt_metrics.json"):
        """Save metrics to file"""
        data = {
            'metrics': [m.to_dict() for m in self.metrics_history],
            'last_updated': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logging.info(f"Metrics saved to {filename}")
    
    def load_metrics(self, filename: str = "simple_prompt_metrics.json"):
        """Load metrics from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            self.metrics_history = []
            for metric_data in data.get('metrics', []):
                metric = PromptMetrics(
                    version=metric_data['version'],
                    word_count=metric_data['word_count'],
                    character_count=metric_data['character_count'],
                    accuracy=metric_data['accuracy'],
                    response_time=metric_data['response_time'],
                    error_rate=metric_data['error_rate'],
                    date=datetime.fromisoformat(metric_data['date'])
                )
                self.metrics_history.append(metric)
            
            logging.info(f"Loaded {len(self.metrics_history)} metrics from {filename}")
        except FileNotFoundError:
            logging.warning(f"Metrics file {filename} not found")
        except Exception as e:
            logging.error(f"Error loading metrics: {e}")

def main():
    """Example usage of the SimplePromptOptimizer"""
    optimizer = SimplePromptOptimizer()
    
    # Example prompts
    original_prompt = """You are an expert SQL analyst for a human resources system.
Based on the schema provided above, please generate a SQL query to answer the following question.
Use only the tables and columns that are relevant to the question.
Please ensure the query is optimized and follows best practices."""

    # Analyze the original prompt
    print("=== Original Prompt Analysis ===")
    analysis = optimizer.analyze_prompt(original_prompt)
    print(f"Words: {analysis['word_count']}")
    print(f"Estimated tokens: {analysis['estimated_tokens']:.1f}")
    print(f"Suggestions: {len(analysis['optimization_suggestions'])}")
    for suggestion in analysis['optimization_suggestions']:
        print(f"- {suggestion['suggestion']}")
    
    # Optimize the prompt
    print("\n=== Prompt Optimization ===")
    optimized_prompt, optimizations = optimizer.optimize_prompt(original_prompt, target_words=50)
    print(f"Original words: {optimizations['original_words']}")
    print(f"Optimized words: {optimizations['final_words']}")
    print(f"Reduction: {optimizations['reduction_percentage']:.1f}%")
    print(f"Optimized prompt: {optimized_prompt}")
    
    # Generate domain-specific prompt
    print("\n=== Domain-Specific Prompt ===")
    sample_schema = {
        'tables': {
            'employees': {
                'columns': {
                    'id': {'type': 'INT', 'nullable': False},
                    'name': {'type': 'VARCHAR(100)', 'nullable': False},
                    'department_id': {'type': 'INT', 'nullable': True}
                }
            }
        }
    }
    
    domain_prompt = optimizer.generate_domain_specific_prompt(
        'hr', 'Show all employees', sample_schema
    )
    print(f"Domain prompt: {domain_prompt}")
    print(f"Words: {len(domain_prompt.split())}")
    
    # Generate report
    print("\n=== Optimization Report ===")
    report = optimizer.generate_optimization_report()
    print(report)

if __name__ == "__main__":
    main() 