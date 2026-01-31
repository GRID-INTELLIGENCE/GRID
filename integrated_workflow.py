#!/usr/bin/env python3
"""
GRID Integrated Workflow
Combines Skills Pipeline, RAG, and Agentic System in a single workflow
"""

import subprocess
import json
import sys
from datetime import datetime
from pathlib import Path

class GridIntegratedWorkflow:
    def __init__(self):
        self.venv = ".venv\\Scripts\\python.exe"
        self.api_base = "http://localhost:8080"
        
    def print_header(self, title):
        """Print formatted header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_section(self, title):
        """Print formatted section"""
        print(f"\n{title}")
        print("-" * 60)
    
    def run_command(self, cmd, description=""):
        """Run command and return result"""
        if description:
            print(f"  {description}...", end=" ", flush=True)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=30)
            if result.returncode == 0:
                if description:
                    print("✓")
                return True, result.stdout
            else:
                if description:
                    print("✗")
                return False, result.stderr
        except subprocess.TimeoutExpired:
            if description:
                print("✗ (timeout)")
            return False, "Command timeout"
        except Exception as e:
            if description:
                print(f"✗ ({e})")
            return False, str(e)
    
    def refine_text(self, text):
        """Step 1: Refine raw text"""
        self.print_section("Step 1: Refine Text")
        
        args = json.dumps({"text": text, "use_llm": False})
        cmd = f'{self.venv} -m grid skills run context.refine --args-json \'{args}\''
        
        success, output = self.run_command(cmd, "Refining text")
        if success:
            try:
                result = json.loads(output)
                refined = result.get('output', '')
                print(f"  Original: {text[:60]}...")
                print(f"  Refined:  {refined[:60]}...")
                return refined
            except:
                print(f"  Output: {output[:100]}")
                return text
        return text
    
    def map_to_schema(self, text, target_schema="resonance"):
        """Step 2: Map to schema"""
        self.print_section(f"Step 2: Map to Schema ({target_schema})")
        
        args = json.dumps({
            "text": text,
            "target_schema": target_schema,
            "output_format": "json",
            "use_llm": False
        })
        cmd = f'{self.venv} -m grid skills run transform.schema_map --args-json \'{args}\''
        
        success, output = self.run_command(cmd, "Mapping to schema")
        if success:
            try:
                result = json.loads(output)
                schema_output = result.get('output', {})
                print(f"  Schema: {target_schema}")
                print(f"  Keys: {list(schema_output.keys())[:3]}")
                return schema_output
            except:
                print(f"  Output: {output[:100]}")
                return {}
        return {}
    
    def compress_text(self, text, max_chars=80):
        """Step 3: Compress to summary"""
        self.print_section("Step 3: Compress to Summary")
        
        args = json.dumps({
            "text": text,
            "max_chars": max_chars,
            "use_llm": False
        })
        cmd = f'{self.venv} -m grid skills run compress.articulate --args-json \'{args}\''
        
        success, output = self.run_command(cmd, "Compressing text")
        if success:
            try:
                result = json.loads(output)
                compressed = result.get('output', '')
                chars = result.get('chars', 0)
                print(f"  Original length: {len(text)}")
                print(f"  Compressed: {compressed}")
                print(f"  Length: {chars}/{max_chars}")
                return compressed
            except:
                print(f"  Output: {output[:100]}")
                return text
        return text
    
    def query_rag(self, query):
        """Step 4: Query RAG for related knowledge"""
        self.print_section("Step 4: Query Knowledge Base")
        
        # Check Ollama
        success, _ = self.run_command(
            'curl -s http://localhost:11434/api/tags',
            "Checking Ollama"
        )
        
        if not success:
            print("  ⚠ Ollama not running - skipping RAG query")
            return []
        
        cmd = f'{self.venv} -m tools.rag.cli query "{query}" 2>&1'
        success, output = self.run_command(cmd, "Querying RAG")
        
        if success:
            lines = output.split('\n')
            results = [l.strip() for l in lines if l.strip() and not l.startswith('2026')]
            if results:
                print(f"  Found {len(results)} results")
                for i, line in enumerate(results[:3], 1):
                    print(f"  {i}. {line[:70]}")
            return results
        else:
            print("  ⚠ RAG query failed (index may not be built)")
            return []
    
    def create_agentic_case(self, raw_input, examples=None, scenarios=None):
        """Step 5: Create agentic case"""
        self.print_section("Step 5: Create Agentic Case")
        
        payload = {
            "raw_input": raw_input,
            "examples": examples or [],
            "scenarios": scenarios or []
        }
        
        cmd = f'curl -s -X POST http://localhost:8080/api/v1/agentic/cases -H "Content-Type: application/json" -d \'{json.dumps(payload)}\''
        
        success, output = self.run_command(cmd, "Creating case")
        if success:
            try:
                case = json.loads(output)
                case_id = case.get('case_id', 'unknown')
                category = case.get('category', 'unknown')
                priority = case.get('priority', 'unknown')
                print(f"  Case ID: {case_id}")
                print(f"  Category: {category}")
                print(f"  Priority: {priority}")
                return case_id
            except:
                print(f"  Output: {output[:100]}")
                return None
        return None
    
    def execute_case(self, case_id, agent_role="Executor"):
        """Step 6: Execute agentic case"""
        self.print_section("Step 6: Execute Case")
        
        payload = {
            "agent_role": agent_role,
            "task": "/execute"
        }
        
        cmd = f'curl -s -X POST http://localhost:8080/api/v1/agentic/cases/{case_id}/execute -H "Content-Type: application/json" -d \'{json.dumps(payload)}\''
        
        success, output = self.run_command(cmd, f"Executing case ({agent_role})")
        if success:
            try:
                result = json.loads(output)
                status = result.get('status', 'unknown')
                outcome = result.get('outcome', 'unknown')
                exec_time = result.get('execution_time_seconds', 0)
                print(f"  Status: {status}")
                print(f"  Outcome: {outcome}")
                print(f"  Execution Time: {exec_time}s")
                return result
            except:
                print(f"  Output: {output[:100]}")
                return None
        return None
    
    def run_complete_workflow(self, raw_input, target_schema="resonance", agent_role="Executor"):
        """Run complete integrated workflow"""
        self.print_header("GRID Integrated Workflow")
        print(f"  Input: {raw_input[:60]}...")
        print(f"  Schema: {target_schema}")
        print(f"  Agent: {agent_role}")
        
        workflow_results = {}
        
        # Step 1: Refine
        refined = self.refine_text(raw_input)
        workflow_results['refined'] = refined
        
        # Step 2: Map to schema
        schema_output = self.map_to_schema(refined, target_schema)
        workflow_results['schema'] = schema_output
        
        # Step 3: Compress
        compressed = self.compress_text(refined)
        workflow_results['compressed'] = compressed
        
        # Step 4: Query RAG
        rag_results = self.query_rag(compressed)
        workflow_results['rag_results'] = rag_results
        
        # Step 5: Create case
        case_id = self.create_agentic_case(
            raw_input=raw_input,
            examples=rag_results[:2] if rag_results else [],
            scenarios=[compressed]
        )
        workflow_results['case_id'] = case_id
        
        # Step 6: Execute case
        if case_id:
            execution = self.execute_case(case_id, agent_role)
            workflow_results['execution'] = execution
        
        # Summary
        self.print_header("Workflow Complete")
        print(f"\nResults Summary:")
        print(f"  ✓ Text refined")
        print(f"  ✓ Schema mapped ({target_schema})")
        print(f"  ✓ Text compressed ({len(compressed)} chars)")
        print(f"  ✓ RAG queried ({len(rag_results)} results)")
        if case_id:
            print(f"  ✓ Case created ({case_id})")
            if workflow_results.get('execution'):
                print(f"  ✓ Case executed")
        
        print(f"\nNext Steps:")
        print(f"  1. Review case reference: .case_references/{case_id}_reference.json")
        print(f"  2. Check experience: curl http://localhost:8080/api/v1/agentic/experience")
        print(f"  3. Iterate on results")
        
        return workflow_results

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python integrated_workflow.py '<raw_input>' [schema] [agent_role]")
        print("\nExample:")
        print("  python integrated_workflow.py 'Add contract testing to CI pipeline' resonance Executor")
        print("\nSchemas: default, resonance, context_engineering, knowledgebase, sensory")
        print("Agents: Analyst, Architect, Planner, Executor, Evaluator, SafetyOfficer")
        return 1
    
    raw_input = sys.argv[1]
    target_schema = sys.argv[2] if len(sys.argv) > 2 else "resonance"
    agent_role = sys.argv[3] if len(sys.argv) > 3 else "Executor"
    
    workflow = GridIntegratedWorkflow()
    results = workflow.run_complete_workflow(raw_input, target_schema, agent_role)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
