# Fixes for open generalaction/emdash issues

Six patches against emdash `main` at `e21cd3d` (v1.2.9), one commit per issue, each
with tests. They were built and tested in a clone of emdash; this session has no push
access to `generalaction/emdash`, so they are delivered here as `git format-patch`
output.

| Patch | Issue | Change |
| --- | --- | --- |
| 0001 | [#3345](https://github.com/generalaction/emdash/issues/3345) | Honor `core.sshCommand`; only export `GIT_SSH_COMMAND='ssh -o BatchMode=yes'` when nothing else picks an ssh command |
| 0002 | [#3339](https://github.com/generalaction/emdash/issues/3339) | `createWorktree` Wire call gets a 10-minute deadline instead of the 30s default |
| 0003 | [#3247](https://github.com/generalaction/emdash/issues/3247) | `git worktree prune` before `worktree add` so orphaned admin refs don't block task creation |
| 0004 | [#3315](https://github.com/generalaction/emdash/issues/3315) | Forward `SystemDrive`, `ProgramData`, `ProgramFiles*` etc. to agents on Windows |
| 0005 | [#3192](https://github.com/generalaction/emdash/issues/3192) | Credential helper reports an unreachable desktop on stderr (naming the loopback address) instead of failing silently |
| 0006 | [#3262](https://github.com/generalaction/emdash/issues/3262) | Usage scan skips nested linked worktrees (no double walk) and honors `AbortSignal` |

Not patched: [#3198](https://github.com/generalaction/emdash/issues/3198) is already
fixed on `main` (`getDefaultBranch` verifies the symref target and falls back to
`git remote show`).

## Apply

```sh
git clone https://github.com/<your-fork>/emdash && cd emdash
git checkout -b fix/open-issues-batch
git am /path/to/emdash-fixes/*.patch
pnpm install
pnpm --dir packages/core exec vitest run \
  src/runtimes/git/node/exec src/runtimes/git/node/git-runtime.test.ts \
  src/services/fs-usage src/primitives/git-credentials src/primitives/agent-env \
  src/runtimes/workspace-registry/node/create-worktree.test.ts
```

Each patch stands alone, so they can be opened as six separate PRs upstream.

## Verification done here

- `@emdash/core` typecheck (`tsgo --noEmit`) and `oxlint` on all touched paths: clean.
- `oxfmt --check` on all touched files: clean.
- Vitest: the touched suites pass (git-exec 7, git-runtime 21, fs-usage 3,
  git-credentials 14, agent-env, create-worktree 9). One existing git-runtime test was
  adjusted to ignore the new `config --get core.sshCommand` probe call.
- Not run: the workspace-registry suites that import `better-sqlite3` (the native
  module did not build in this container) and the desktop typecheck (hundreds of
  pre-existing errors from unbuilt `@emdash/ui` types; none in the touched file).
