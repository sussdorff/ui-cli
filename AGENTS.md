# Agent Instructions

Track work in hosted issues through `ccore tracker`. Use full issue references
in the form `sussdorff/ui-cli#N`.

## Quick Reference

```bash
ccore tracker list --repo sussdorff/ui-cli
ccore tracker show sussdorff/ui-cli#N
ccore tracker create --repo sussdorff/ui-cli --body-file <file>
ccore tracker close sussdorff/ui-cli#N
```

## Session Completion

Use the installed delivery workflow for verification, review and pull request
publication. Run the installed session-retro skill after delivery. Report the
pull request's merge state and any project-specific postconditions. Preserve
existing authorization for the same concrete scope and never discard foreign
or uncommitted work during cleanup.
