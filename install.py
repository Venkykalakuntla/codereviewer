#!/usr/bin/env python3

import os
import sys
import subprocess
import platform

def main():
    """Install the GitHub PR code review agent and its dependencies."""
    print("Installing GitHub PR Code Review Agent...")
    
    # Determine the Python executable
    python_exe = sys.executable
    print(f"Using Python: {python_exe}")
    
    # Create virtual environment
    venv_dir = os.path.join(os.path.dirname(__file__), 'venv')
    if not os.path.exists(venv_dir):
        print("Creating virtual environment...")
        subprocess.run([python_exe, '-m', 'venv', venv_dir], check=True)
    
    # Determine the pip executable in the virtual environment
    if platform.system() == 'Windows':
        pip_exe = os.path.join(venv_dir, 'Scripts', 'pip')
        activate_script = os.path.join(venv_dir, 'Scripts', 'activate')
    else:
        pip_exe = os.path.join(venv_dir, 'bin', 'pip')
        activate_script = os.path.join(venv_dir, 'bin', 'activate')
    
    # Install dependencies
    print("Installing dependencies...")
    requirements_file = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    subprocess.run([pip_exe, 'install', '-r', requirements_file], check=True)
    
    # Install the package in development mode
    print("Installing package in development mode...")
    subprocess.run([pip_exe, 'install', '-e', '.'], check=True)
    
    # Create .env file if it doesn't exist
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    env_example_file = os.path.join(os.path.dirname(__file__), '.env.example')
    
    if not os.path.exists(env_file) and os.path.exists(env_example_file):
        print("Creating .env file from .env.example...")
        with open(env_example_file, 'r') as example_file:
            example_content = example_file.read()
        
        with open(env_file, 'w') as env_file_obj:
            env_file_obj.write(example_content)
        
        print(".env file created. Please edit it to add your GitHub credentials.")
    
    print("\nInstallation completed successfully!")
    print(f"\nTo activate the virtual environment, run:")
    if platform.system() == 'Windows':
        print(f"    {activate_script}")
    else:
        print(f"    source {activate_script}")
    
    print("\nTo run the code review agent, use:")
    print("    python src/main.py --help")
    
    print("\nTo run the test script, use:")
    print("    python test_review.py [PR_NUMBER]")

if __name__ == '__main__':
    main()