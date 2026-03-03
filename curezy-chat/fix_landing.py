import os

filepath = r"e:\Curezy-ai\curezy-chat\src\pages\Landing.jsx"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# lines is 0-indexed.
# Line 183 is index 182.
# Line 270 is index 269.
# We want to keep up to index 182 (so lines[:182])
# We want to drop index 182 through 269.
# We want to keep from index 270 onwards (so lines[270:])

new_lines = lines[:182] + ["            {/* Unified AI Pipeline (Morphing) */}\n", "            <UnifiedPipeline />\n\n"] + lines[270:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Landing.jsx fixed.")
