"""
Fix the split fast_stream yield line in main.py.
The line was split across two physical lines due to CRLF line endings.
After fix, the string emits proper SSE: data: {...}\n\n
"""
with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# The problematic string spans 2 lines:
# Line A: `            yield f'data: {json.dumps(...)}`
# Line B: `\n\n'`
# We want it on one logical line. Find the specific split.

OLD = (
    "            yield f'data: {json.dumps({\"type\":\"result\", \"data\": "
    "{\"success\": True, \"message\": result_dict[\"response\"], "
    "\"stage\": result_dict[\"stage\"], \"stage_metadata\": result_dict[\"stage_metadata\"]}})}\r\n"
    "\\n\\n'\r\n"
)
NEW = (
    "            yield f'data: {json.dumps({\"type\":\"result\", \"data\": "
    "{\"success\": True, \"message\": result_dict[\"response\"], "
    "\"stage\": result_dict[\"stage\"], \"stage_metadata\": result_dict[\"stage_metadata\"]}})}\\n\\n'\r\n"
)

if OLD in content:
    content = content.replace(OLD, NEW, 1)
    print("[OK] fast_stream yield fixed")
else:
    # Try without \r
    OLD2 = (
        "            yield f'data: {json.dumps({\"type\":\"result\", \"data\": "
        "{\"success\": True, \"message\": result_dict[\"response\"], "
        "\"stage\": result_dict[\"stage\"], \"stage_metadata\": result_dict[\"stage_metadata\"]}})}\n"
        "\\n\\n'\n"
    )
    NEW2 = (
        "            yield f'data: {json.dumps({\"type\":\"result\", \"data\": "
        "{\"success\": True, \"message\": result_dict[\"response\"], "
        "\"stage\": result_dict[\"stage\"], \"stage_metadata\": result_dict[\"stage_metadata\"]}})}\\n\\n'\n"
    )
    if OLD2 in content:
        content = content.replace(OLD2, NEW2, 1)
        print("[OK] fast_stream yield fixed (LF variant)")
    else:
        print("[WARN] Pattern not found. Showing fast_stream context:")
        idx = content.find("fast_stream")
        print(repr(content[idx:idx+300]))

with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Done.")
