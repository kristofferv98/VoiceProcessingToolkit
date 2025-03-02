#!/usr/bin/env python
"""
Script to run tests for the VoiceProcessingToolkit.
"""
import os
import subprocess
import sys
from termcolor import colored

def run_tests():
    """Run the test suite."""
    # Print header
    print(colored("\n=== VoiceProcessingToolkit Test Suite ===", "cyan", attrs=["bold"]))
    print(colored("Running tests...", "cyan"))
    
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Run pytest
    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "-v"],
            cwd=os.path.dirname(script_dir),  # Run from project root
            check=False,
            capture_output=True,
            text=True
        )
        
        # Print test results
        if result.returncode == 0:
            print(colored("\n✓ All tests passed!", "green", attrs=["bold"]))
            print(colored(result.stdout, "green"))
        else:
            print(colored("\n✗ Some tests failed!", "red", attrs=["bold"]))
            print(colored(result.stdout, "yellow"))
            print(colored(result.stderr, "red"))
        
        return result.returncode
    except Exception as e:
        print(colored(f"\n✗ Error running tests: {e}", "red", attrs=["bold"]))
        return 1

if __name__ == "__main__":
    sys.exit(run_tests()) 