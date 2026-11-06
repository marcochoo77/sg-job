#!/usr/bin/env bash
# Upload this project to https://github.com/marchoo77/sg-job (SSH).
# Safe to re-run: it skips steps already completed.
#
# Usage:
#   chmod +x upload_to_github.sh
#   ./upload_to_github.sh

set -euo pipefail

REPO_OWNER="marchoo77"
REPO_NAME="sg-job"
SSH_URL="git@github.com:${REPO_OWNER}/${REPO_NAME}.git"

# ---- colours ----
info()  { printf "\033[1;34m[info]\033[0m  %s\n" "$*"; }
ok()    { printf "\033[1;32m[ok]\033[0m    %s\n" "$*"; }
warn()  { printf "\033[1;33m[warn]\033[0m  %s\n" "$*"; }
err()   { printf "\033[1;31m[err]\033[0m   %s\n" "$*" >&2; }

# ---- 0. sanity ----
command -v git >/dev/null || { err "git not installed"; exit 1; }
[ -f "app.py" ] || { err "Run this script from the project root (app.py not found)."; exit 1; }
[ -f ".gitignore" ] || warn ".gitignore missing — large data files may be committed."

# ---- 1. git identity ----
if ! git config --global user.name >/dev/null; then
  read -rp "Your git user.name  [${REPO_OWNER}]: " NAME
  git config --global user.name "${NAME:-$REPO_OWNER}"
fi
if ! git config --global user.email >/dev/null; then
  read -rp "Your git user.email: " EMAIL
  [ -n "$EMAIL" ] && git config --global user.email "$EMAIL"
fi
info "git identity: $(git config --global user.name) <$(git config --global user.email)>"

# ---- 2. SSH check ----
info "Testing SSH to github.com …"
if ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
  ok "SSH key works with GitHub."
else
  warn "SSH test did not confirm 'successfully authenticated'."
  warn "Trying to load your key into ssh-agent …"
  eval "$(ssh-agent -s)" >/dev/null
  for k in "$HOME"/.ssh/id_ed25519 "$HOME"/.ssh/id_rsa; do
    [ -f "$k" ] && ssh-add "$k" 2>/dev/null || true
  done
  if ssh -o BatchMode=yes -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
    ok "SSH key now works."
  else
    err "SSH to GitHub failed. Add your public key at https://github.com/settings/keys"
    err "Then re-run this script."
    exit 1
  fi
fi

# ---- 3. init repo ----
if [ ! -d ".git" ]; then
  info "git init"
  git init -q
fi

# ---- 4. branch main ----
git symbolic-ref -q HEAD >/dev/null || true
git branch -M main

# ---- 5. remote ----
if git remote get-url origin >/dev/null 2>&1; then
  CURRENT=$(git remote get-url origin)
  if [ "$CURRENT" != "$SSH_URL" ]; then
    info "Updating origin: $CURRENT → $SSH_URL"
    git remote set-url origin "$SSH_URL"
  fi
else
  info "Adding remote origin → $SSH_URL"
  git remote add origin "$SSH_URL"
fi
ok "origin = $(git remote get-url origin)"

# ---- 6. safety: no big data files tracked ----
BIG=$(git ls-files 2>/dev/null | grep -E '^(data/.*\.(csv|zip)|.*\.duckdb(\.wal)?)$' || true)
if [ -n "$BIG" ]; then
  warn "These data files are tracked and should be removed:"
  echo "$BIG"
  read -rp "Remove them from git index now? [Y/n]: " ANS
  if [[ "${ANS:-Y}" =~ ^[Yy]$ ]]; then
    echo "$BIG" | xargs -r git rm --cached --
    ok "Removed from index (files kept on disk)."
  fi
fi

# ---- 7. stage + commit ----
git add .
if git diff --cached --quiet; then
  info "Nothing new to commit."
else
  COMMIT_MSG="Update SG Jobs Analytics — $(date '+%Y-%m-%d %H:%M')"
  git commit -q -m "$COMMIT_MSG"
  ok "Committed: $COMMIT_MSG"
fi

# ---- 8. push ----
info "Pushing to $SSH_URL (branch main) …"
if git ls-remote --exit-code --heads origin main >/dev/null 2>&1; then
  git pull --rebase origin main || true
fi
git push -u origin main

ok "Done."
echo
echo "Repo:  https://github.com/${REPO_OWNER}/${REPO_NAME}"
echo "SSH:   ${SSH_URL}"