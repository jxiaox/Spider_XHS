import re

path = 'initial_state.txt'
try:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to find xsecToken
    # Look for "xsecToken":"..."
    matches = re.finditer(r'"xsecToken":"([^"]+)"', content)
    
    print("Found tokens:")
    for m in matches:
        token = m.group(1)
        # Show context (prev 50 chars)
        start = max(0, m.start() - 50)
        context = content[start:m.start()]
        print(f"Context: {context} => Token: {token[:20]}...")
        
        if "user" in context or "User" in context:
             print("^^^ POTENTIAL USER TOKEN ^^^")

except Exception as e:
    print(f"Error: {e}")
