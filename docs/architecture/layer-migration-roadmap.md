# Layer Migration Roadmap

This document defines the target context-first structure for the service.

## Target
- application/<context>
- domain/<context>
- infrastructure/<context>

## Migration rules
1. Keep API contracts stable while moving internals.
2. Move by context in small slices (no big-bang).
3. Keep old imports as compatibility shims until all call sites are moved.
4. Remove shims only after test and contract checks are green.
