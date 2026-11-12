#!/usr/bin/env bash
# Push the four UnitcellMD workspace repositories to GitHub: all local branches and tags, over
# SSH (git@github.com:OWNER/NAME.git). Idempotent, so it is also the command for later pushes.
#
#   tools/publish-github.sh [--owner NAME] [--private] [--prs] [--dry-run]
#
#   --owner NAME  GitHub organization or user that hosts the repos (default: mines-of-morja)
#   --private     create missing repos as private. Default: public, like the existing repos.
#                 The visibility of existing repos is never changed.
#   --prs         open a pull request into main for every other branch that has none (needs gh)
#   --dry-run     check everything, print what would be created and pushed, change nothing
#
# Missing repos are created with gh when it is logged in (`gh auth login`). Without gh, create
# them in the web UI as empty repos (no README, licence or .gitignore) and run the script again.
set -euo pipefail

OWNER=mines-of-morja
VISIBILITY=--public
PRS=0
DRY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --owner) OWNER=${2:?--owner needs a name}; shift 2 ;;
    --private) VISIBILITY=--private; shift ;;
    --prs) PRS=1; shift ;;
    --dry-run) DRY=1; shift ;;
    -h | --help) sed -n '2,15p' "$0"; exit 0 ;;
    *) echo "unknown option: $1 (see --help)" >&2; exit 2 ;;
  esac
done

cd "$(dirname "$0")/.."

REPOS=(UnitcellMD ucmd-engine ucmd-builder ucmd-analysis)
declare -A DIR=([UnitcellMD]=. [ucmd-engine]=ucmd-engine [ucmd-builder]=ucmd-builder [ucmd-analysis]=ucmd-analysis)
declare -A DESC=(
  [UnitcellMD]="Modular MD ecosystem: plan, shared spec (formats, units, force-provider contract), fixtures"
  [ucmd-engine]="UnitcellMD MD engine (Rust): integrators, thermostats, interchangeable force providers"
  [ucmd-builder]="UnitcellMD system builder (Python): molecules, electrolytes, crystals, force-field templates, GUI"
  [ucmd-analysis]="UnitcellMD trajectory analysis (Python): structure, diffusion, Onsager transport coefficients"
)

run() { if [[ $DRY == 1 ]]; then echo "  would run: $*"; else "$@"; fi; }

# "owner/name" of a GitHub remote URL (HTTPS or SSH form), lower-case; empty for anything else.
slug() {
  local s
  s=$(sed -nE 's#^(https://github\.com/|git@github\.com:|ssh://git@github\.com/)([^/]+/[^/]+)$#\2#p' <<<"${1%.git}")
  echo "${s,,}"
}

HAVE_GH=0
if command -v gh >/dev/null && gh auth status >/dev/null 2>&1; then HAVE_GH=1; fi
if [[ $PRS == 1 && $HAVE_GH == 0 ]]; then
  echo "--prs needs gh: run 'gh auth login' first." >&2
  exit 1
fi

# 1. Check everything before changing anything.
for name in "${REPOS[@]}"; do
  dir=${DIR[$name]}
  if [[ ! -d "$dir/.git" ]]; then
    echo "$dir is not a git repository (workspace layout: see CLAUDE.md)." >&2
    exit 1
  fi
  if git -C "$dir" rev-parse --verify --quiet refs/heads/main >/dev/null; then :; else
    echo "$dir has no branch main." >&2
    exit 1
  fi
  if url=$(git -C "$dir" remote get-url origin 2>/dev/null); then
    if [[ "$(slug "$url")" != "${OWNER,,}/${name,,}" ]]; then
      echo "$dir: origin is $url, not $OWNER/$name. Pass the right --owner or fix the remote." >&2
      exit 1
    fi
  fi
done

auth=$(ssh -T -o BatchMode=yes git@github.com 2>&1 || true)
if [[ $auth != *"successfully authenticated"* ]]; then
  echo "SSH access to GitHub does not work: ${auth}" >&2
  exit 1
fi
echo "SSH: ${auth%%!*}"

missing=()
for name in "${REPOS[@]}"; do
  if git ls-remote "git@github.com:$OWNER/$name.git" >/dev/null 2>&1; then continue; fi
  if [[ $HAVE_GH == 1 ]]; then
    run gh repo create "$OWNER/$name" "$VISIBILITY" --description "${DESC[$name]}"
  else
    missing+=("$OWNER/$name")
  fi
done
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "Not on GitHub yet. Create each at https://github.com/new as an empty repo (no README," >&2
  echo "licence or .gitignore; visibility ${VISIBILITY#--}), then run this script again:" >&2
  printf '  %s\n' "${missing[@]}" >&2
  [[ $DRY == 1 ]] || exit 1
fi

# 2. Point origin at the SSH URL and push. main goes first, so a new repo gets it as default.
for name in "${REPOS[@]}"; do
  dir=${DIR[$name]}
  ssh_url="git@github.com:$OWNER/$name.git"
  echo "== $OWNER/$name ($dir): branches $(git -C "$dir" for-each-ref --format='%(refname:short)' refs/heads | tr '\n' ' ')"
  if git -C "$dir" remote get-url origin >/dev/null 2>&1; then
    [[ "$(git -C "$dir" remote get-url origin)" == "$ssh_url" ]] || run git -C "$dir" remote set-url origin "$ssh_url"
  else
    run git -C "$dir" remote add origin "$ssh_url"
  fi
  run git -C "$dir" push -u origin main
  run git -C "$dir" push -u origin --all
  run git -C "$dir" push origin --tags

  # A repo whose first push was another branch has that branch as default; reviews need main.
  default=$(git ls-remote --symref "$ssh_url" HEAD 2>/dev/null | sed -nE 's#^ref: refs/heads/(.+)\tHEAD$#\1#p' || true)
  if [[ -n "$default" && "$default" != main ]]; then
    if [[ $HAVE_GH == 1 ]]; then
      run gh repo edit "$OWNER/$name" --default-branch main
    else
      echo "  default branch on GitHub is '$default': set it to main under Settings > General."
    fi
  fi

  if [[ $PRS == 1 ]]; then
    for branch in $(git -C "$dir" for-each-ref --format='%(refname:short)' refs/heads | grep -vx main || true); do
      if [[ -z "$(gh pr list --repo "$OWNER/$name" --head "$branch" --state open --json number --jq '.[].number')" ]]; then
        run gh pr create --repo "$OWNER/$name" --base main --head "$branch" \
          --title "$branch" \
          --body "Review branch \`$branch\`. What it contains and what needs a decision: docs/STATUS.md in the UnitcellMD repo."
      fi
    done
  fi
done
