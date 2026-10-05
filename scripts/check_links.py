"""Check that each relative link in the tracked Markdown files points to a file that exists."""

import re
import subprocess
import sys
from pathlib import Path

# [text](target): the target stops at a space or a closing parenthesis.
LINK = re.compile(r'\]\(([^)\s]+)\)')

files = subprocess.run(['git', 'ls-files', '*.md'], capture_output=True, text=True, check=True).stdout.split()
broken = []
for name in files:
    path = Path(name)
    in_code = False
    for number, line in enumerate(path.read_text().splitlines(), start=1):
        if line.lstrip().startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            continue
        for target in LINK.findall(line):
            if re.match(r'[a-z]+:', target) or target.startswith('#'):
                continue  # a URL, or an anchor in the same file
            local = re.sub(r'(#.*|:\d+)$', '', target)
            if not (path.parent / local).exists():
                broken.append(f'{name}:{number}: {target}')

for item in broken:
    print(f'error  link: {item}', file=sys.stderr)
if broken:
    sys.exit(1)
print(f'ok    links in {len(files)} Markdown files')
