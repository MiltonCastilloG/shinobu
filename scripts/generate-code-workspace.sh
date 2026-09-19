#!/usr/bin/env bash
# Regenerate shinobu.code-workspace from worktrees/ — run after add/remove worktrees.
set -euo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
python3 -c "import json; from pathlib import Path; wt=Path('worktrees'); folders=[{'name':'Shared','path':'.'}]+([{'name':p.name,'path':f'worktrees/{p.name}'} for p in sorted(wt.iterdir()) if p.is_dir() and (p/'.git').exists()] if wt.is_dir() else []); Path('shinobu.code-workspace').write_text(json.dumps({'folders':folders,'settings':{'git.autoRepositoryDetection':True}},indent=2)+'\n'); print(f'Wrote shinobu.code-workspace — Shared + {len(folders)-1} worktree(s)')"
