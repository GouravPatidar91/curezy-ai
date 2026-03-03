import os

filepath = r"e:\Curezy-ai\curezy-chat\src\pages\Landing.jsx"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# REMOVE PIPELINE_STEPS block
s_idx = content.find("const PIPELINE_STEPS = [")
e_idx = content.find("const FEATURES = [")
if s_idx != -1 and e_idx != -1:
    content = content[:s_idx] + content[e_idx:]

# REMOVE PIPELINE VISUALS
s_idx = content.find("function PipelineVisuals")
e_idx = content.find("const FULL_PROMPT =")
if s_idx != -1 and e_idx != -1:
    content = content[:s_idx] + content[e_idx:]

# REMOVE PROMPT TRANSITION
s_idx = content.find("const FULL_PROMPT =")
e_idx = content.find("export default function Landing()")
if s_idx != -1 and e_idx != -1:
    content = content[:s_idx] + content[e_idx:]

# REPLACE THE JSX INSIDE LANDING
s_idx = content.find("{/* Scroll Mockup Transition */}")
if s_idx == -1: s_idx = content.find("<PromptTransition />") - 10

e_idx = content.find("{/* 3. Features Grid")
if s_idx != -1 and e_idx != -1:
    unified_calls = "            {/* Unified AI Pipeline (Morphing) */}\n            <UnifiedPipeline />\n\n            "
    content = content[:s_idx] + unified_calls + content[e_idx:]

# ADD IMPORT
if "import UnifiedPipeline" not in content:
    idx = content.find("import {")
    content = content[:idx] + "import UnifiedPipeline from '../components/UnifiedPipeline';\n" + content[idx:]

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Landing.jsx cleaned and UnifiedPipeline integrated successfully.")
