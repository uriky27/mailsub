#!/usr/bin/env bash
set -euo pipefail

REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_HOST="${REMOTE_HOST:-your-server-host}"
REMOTE_PATH="${REMOTE_PATH:-/opt/mailsub}"
REMOTE_BRANCH="${REMOTE_BRANCH:-main}"
GIT_REPO_URL="${GIT_REPO_URL:-$(git config --get remote.origin.url 2>/dev/null || echo "https://github.com/your-user/mailsub.git") }"

if [[ -z "${REMOTE_USER}" || -z "${REMOTE_HOST}" || "${REMOTE_HOST}" == "your-server-host" ]]; then
  echo "Configure REMOTE_USER and REMOTE_HOST before running deploy."
  echo "Example:"
  echo "  REMOTE_USER=deploy REMOTE_HOST=123.45.67.89 ./scripts/deploy.sh"
  exit 1
fi

if [[ -z "${GIT_REPO_URL}" || "${GIT_REPO_URL}" == " " ]]; then
  echo "Unable to determine Git remote URL. Set GIT_REPO_URL explicitly."
  exit 1
fi

if [[ "${GIT_REPO_URL}" == *"your-user"* || "${GIT_REPO_URL}" == *"/mailsub.git"* && "${GIT_REPO_URL}" == *"your-user"* ]]; then
  echo "ERROR: You are still using the placeholder GitHub URL. Replace it with your real repository URL."
  echo "Examples:"
  echo "  https://github.com/your-name/mailsub.git"
  echo "  git@github.com:your-name/mailsub.git"
  exit 1
fi

GIT_REPO_URL="${GIT_REPO_URL%%[[:space:]]*}"

REMOTE_BOOTSTRAP='set -e;
if ! command -v git >/dev/null 2>&1 || ! command -v python3 >/dev/null 2>&1; then
  if command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y git python3 python3-pip || true;
    sudo dnf install -y python3-virtualenv || sudo dnf install -y python3-venv || sudo dnf install -y python3-devel;
  elif command -v yum >/dev/null 2>&1; then
    sudo yum install -y git python3 python3-pip || true;
    sudo yum install -y python3-virtualenv || sudo yum install -y python3-venv || sudo yum install -y python3-devel;
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update;
    sudo apt-get install -y git python3 python3-pip python3-venv;
  else
    echo "Unsupported OS: neither apt-get, dnf nor yum is available.";
    exit 1;
  fi;
fi;
if [ ! -d "'"${REMOTE_PATH}"'/.git" ]; then
  sudo mkdir -p "'"${REMOTE_PATH}"'";
  if ! sudo git clone "'"${GIT_REPO_URL}"'" "'"${REMOTE_PATH}"'"; then
    echo "Git clone failed. This usually means the repository is private, the URL is wrong, or GitHub auth is missing.";
    echo "Use either a public repo URL or an SSH URL with keys configured on the server.";
    exit 1;
  fi;
fi'

echo "Deploying to ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}"

echo "1/5. Bootstrap remote server if needed"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "bash -lc '${REMOTE_BOOTSTRAP}'"

echo "2/5. Pulling latest code from ${REMOTE_BRANCH}"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "bash -lc 'set -e; cd \"${REMOTE_PATH}\"; git fetch --all --prune; git checkout \"${REMOTE_BRANCH}\"; git pull origin \"${REMOTE_BRANCH}\"'"

echo "3/5. Creating venv and installing Python dependencies"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "bash -lc 'set -e; cd \"${REMOTE_PATH}\"; if [ ! -d venv ]; then python3 -m venv venv; fi; . venv/bin/activate; pip install --upgrade pip; pip install -r requirements.txt'"

echo "4/5. Installing systemd service if missing"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "bash -lc 'set -e; if [ ! -f /etc/systemd/system/mailsub.service ]; then sudo cp \"${REMOTE_PATH}/systemd/mailsub.service\" /etc/systemd/system/mailsub.service; fi; if [ -f \"${REMOTE_PATH}/systemd/mailsub.timer\" ] && [ ! -f /etc/systemd/system/mailsub.timer ]; then sudo cp \"${REMOTE_PATH}/systemd/mailsub.timer\" /etc/systemd/system/mailsub.timer; fi; sudo systemctl daemon-reload; sudo systemctl enable mailsub.timer 2>/dev/null || true'"

echo "5/5. Restarting service"
ssh "${REMOTE_USER}@${REMOTE_HOST}" "bash -lc 'set -e; sudo systemctl daemon-reload; sudo systemctl restart mailsub 2>/dev/null || true; sudo systemctl status mailsub --no-pager -l --lines=20 2>/dev/null || true'"

echo "Deployment finished successfully."
echo "Next steps on the server: configure .env and credentials.json in ${REMOTE_PATH}, then run:"
echo "  sudo systemctl restart mailsub"
