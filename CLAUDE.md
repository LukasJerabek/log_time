# Project conventions

## Purpose
- Assistants may make edits to help maintain and develop this Hugo site.

## Scope
- Not allowed: modify `.git/config`, push commits or create PRs, add or change secrets.
- Completely ignore hugo_site/content folder, never search index or anything.

## Behavior rules
- This is minimalistic blog site, keep it simple.
- After completing a task, commit the changes and open a pull request for human review. Do not merge or push directly to master.
- Run `hugo server -D --disableFastRender` to validate visual changes locally.
- When in doubt, open an issue or ask a reviewer.
- There is also .assistant-ignore file in the root, read it pls, it has files to ignore.

## Security & data handling
- Do not read or include secrets, API keys, or private data in prompts or commits.
- Avoid copying external content that may be copyrighted without attribution.

