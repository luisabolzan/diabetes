import os
import subprocess
import sys
from pathlib import Path
import nicegui

def build():
    # Get the path to the nicegui package
    nicegui_path = Path(nicegui.__file__).parent
    
    cmd = [
        'pyinstaller',
        'main.py',
        '--name', 'DiabetesCalculator',
        '--onefile',
        '--windowed', # Hide console
        f'--add-data={nicegui_path}{os.pathsep}nicegui',
    ]
    
    print(f"Running build command: {' '.join(cmd)}")
    subprocess.call(cmd)

if __name__ == '__main__':
    build()
