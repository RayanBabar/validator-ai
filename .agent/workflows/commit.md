---
description: Intelligent commit workflow: analyze change, group by context, commit group by group, and push.
---

1. **Analyze Changes**: 
   - Run `git status` to see modified files.
   - Run `git diff` to inspect specific changes.

2. **Group Changes**: 
   - Identify logical groupings of changes (e.g., by feature, bugfix, or refactor).
   - Plan the order of commits.

3. **Commit Groups**: 
   - For each group:
     - Run `git add <file_paths>` for the files in the group.
     - Run `git commit -m "<descriptive_message>"` explaining the context.
   - Repeat until all changes are committed.

4. **Push**: 
   - Run `git push` to sync the changes.
