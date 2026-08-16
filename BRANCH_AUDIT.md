# Branch and history audit

## Canonical remote state

| Item | Required final state |
|---|---|
| Repository | `MachineLearning-Nerd/icml26-do-shapley` |
| Default branch | `main` |
| Published branches | exactly `main` |
| Retired branch | `master` is removed after migration |
| Generated branch names | none; no `orx` or session-specific branch is retained |
| Commit author and committer | `MachineLearning-Nerd <MachineLearning-Nerd@users.noreply.github.com>` |

The rename preserves the repository's scoped history while making the paper
identity visible in the URL. Branch normalization is deliberately separate
from the paper claims: `main` is the publication branch, and no experiment
branch is presented as a reproducible release path.

## Verification

Run:

```bash
python verify_final.py
```

The verifier checks the local branch/ref namespace, the `origin` URL, all
reachable commit identities, working-tree cleanliness, required documentation,
committed evidence metrics, and the focused test suite. The final GitHub API
branch list and tip are checked separately during publication and recorded in
the collection tracker.
