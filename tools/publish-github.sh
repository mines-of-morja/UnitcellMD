#!/usr/bin/env bash
# Publish the UnitcellMD workspace repositories to the GitHub organization and push all local
# branches. Idempotent: existing GitHub repos and remotes are reused, so it is also the command
# for later pushes.
#
#   tools/publish-github.sh          create missing repos, push main + all other branches + tags
#   tools/publish-github.sh --prs    additionally open a pull request into main for every
#                                    non-main branch that has none yet (review = PR review)
#
# Needs: gh, logged in once with `gh auth login` followed by `gh auth setup-git`.
set -euo pipefail

ORG=mines-of-morja
cd "$(dirname "$0")/.."

REPOS=(UnitcellMD ucmd-engine ucmd-builder ucmd-analysis)
declare -A DIR=([UnitcellMD]=. [ucmd-engine]=ucmd-engine [ucmd-builder]=ucmd-builder [ucmd-analysis]=ucmd-analysis)
declare -A DESC=(
  [UnitcellMD]="Modular MD ecosystem: plan, shared spec (formats, units, force-provider contract), fixtures"
  [ucmd-engine]="UnitcellMD MD engine (Rust): integrators, thermostats, interchangeable force providers"
  [ucmd-builder]="UnitcellMD system builder (Python): molecules, electrolytes, crystals, force-field templates, GUI"
  [ucmd-analysis]="UnitcellMD trajectory analysis (Python): structure, diffusion, Onsager transport coefficients"
)

if ! gh auth status >/dev/null 2>&1; then
  echo "Not logged in to GitHub. Run 'gh auth login' and then 'gh auth setup-git'." >&2
  exit 1
fi

for name in "${REPOS[@]}"; do
  dir=${DIR[$name]}
  echo "== $ORG/$name ($dir)"
  if ! gh repo view "$ORG/$name" >/dev/null 2>&1; then
    gh repo create "$ORG/$name" --public --description "${DESC[$name]}"
  fi
  if ! git -C "$dir" remote get-url origin >/dev/null 2>&1; then
    git -C "$dir" remote add origin "https://github.com/$ORG/$name.git"
  fi
  git -C "$dir" push -u origin main       # main first, so it becomes the default branch
  git -C "$dir" push -u origin --all
  git -C "$dir" push origin --tags

  if [[ "${1:-}" == "--prs" ]]; then
    for branch in $(git -C "$dir" for-each-ref --format='%(refname:short)' refs/heads | grep -vx main || true); do
      if [[ -z "$(gh pr list --repo "$ORG/$name" --head "$branch" --state open --json number --jq '.[].number')" ]]; then
        gh pr create --repo "$ORG/$name" --base main --head "$branch" \
          --title "$branch" \
          --body "Review branch \`$branch\`. What it contains and what needs a decision: docs/STATUS.md in the UnitcellMD repo."
      fi
    done
  fi
done
