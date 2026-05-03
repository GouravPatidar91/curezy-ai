import os
import re

def scrub_file(path):
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Replace common emojis/symbols with ASCII equivalents
    replacements = {
        '[OK]': '[SUCCESS]',
        '[FAIL]': '[ERROR]',
        '[ALERT]': '[ALERT]',
        '[BRAIN]': '[BRAIN]',
        '[DEBATE]': '[DEBATE]',
        '[DEBATE]': '[DEBATE]',
        '[MED]': '[MED]',
        '[SEARCH]': '[SEARCH]',
        '[RX]': '[RX]',
        '[FAST]': '[FAST]',
        '[TIME]': '[TIME]',
        '[TIME]': '[TIME]',
        '[LAB]': '[LAB]',
        '[REPORT]': '[REPORT]',
        '[HOSPITAL]': '[HOSPITAL]',
        '[DOCTOR]': '[DOCTOR]',
        '[DOCTOR]': '[DOCTOR]',
        '[EMERGENCY]': '[EMERGENCY]',
        '[SOS]': '[SOS]',
        '->': '->',
        '--': '--',
        '-': '-',
        '*': '*',
        '[OK]': '[OK]',
        '[FAIL]': '[FAIL]',
        '[WARN]': '[WARN]',
        '[IV]': '[IV]',
        '[PATCH]': '[PATCH]',
        '[TEMP]': '[TEMP]',
        '[TEMP]': '[TEMP]',
    }
    
    new_content = content
    for char, rep in replacements.items():
        new_content = new_content.replace(char, rep)
    
    # Final pass: remove any remaining non-ASCII characters
    new_content = "".join(i for i in new_content if ord(i) < 128)
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Scrubbed: {path}")

def main():
    service_dir = r"e:\Curezy-ai\ai-service"
    for root, dirs, files in os.walk(service_dir):
        if 'venv' in root or '.git' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                scrub_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
