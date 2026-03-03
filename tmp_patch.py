import re
path = r'e:\Curezy-ai\ai-service\main.py'
content = open(path, encoding='utf-8').read()
old = '_run_council_analysis(data.conversation_id, state)'
new = '_run_council_analysis(data.conversation_id, state, data.selected_model)'
if old in content:
    content = content.replace(old, new, 1)
    open(path, 'w', encoding='utf-8').write(content)
    print('PATCHED OK')
else:
    idx = content.find('_run_council_analysis')
    print('NOT FOUND, context:', repr(content[idx:idx+120]))
