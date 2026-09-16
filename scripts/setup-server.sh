#!/usr/bin/env bash
set -euo pipefail

REPO_PATH="${REPO_PATH:-/opt/mailsub}"
BRANCH="${BRANCH:-main}"
GIT_REPO_URL="${GIT_REPO_URL:-https://github.com/your-user/mailsub.git}"

if [[ "$EUID" -ne 0 ]]; then
  echo "Run this script as root or with sudo."
  exit 1
fi

SUDO=""
if command -v sudo >/dev/null 2>&1; then
  SUDO="sudo"
fi

ensure_packages() {
  if command -v dnf >/dev/null 2>&1; then
    echo "Detected RedHat/Fedora-like system via dnf"
    ${SUDO} dnf install -y git python3 python3-pip || true
    ${SUDO} dnf install -y python3-virtualenv || ${SUDO} dnf install -y python3-venv || ${SUDO} dnf install -y python3-devel
  elif command -v yum >/dev/null 2>&1; then
    echo "Detected RedHat/CentOS-like system via yum"
    ${SUDO} yum install -y git python3 python3-pip || true
    ${SUDO} yum install -y python3-virtualenv || ${SUDO} yum install -y python3-venv || ${SUDO} yum install -y python3-devel
  elif command -v apt-get >/dev/null 2>&1; then
    echo "Detected Debian/Ubuntu-like system via apt-get"
    ${SUDO} apt-get update
    ${SUDO} apt-get install -y git python3 python3-pip python3-venv
  else
    echo "Unsupported operating system: neither apt-get, dnf nor yum is available."
    exit 1
  fi
}

echo "Installing Python and git dependencies"
ensure_packages

if [[ ! -d "$REPO_PATH/.git" ]]; then
  git clone "$GIT_REPO_URL" "$REPO_PATH"
fi

cd "$REPO_PATH"
git fetch --all --prune
git checkout "$BRANCH"
git pull origin "$BRANCH"

if [[ ! -d venv ]]; then
  python3 -m venv venv
fi

. venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Server is ready. Configure .env and credentials.json in $REPO_PATH"
echo "Then install the service:"
echo "  cp $REPO_PATH/systemd/mailsub.service /etc/systemd/system/mailsub.service"
echo "  cp $REPO_PATH/systemd/mailsub.timer /etc/systemd/system/mailsub.timer"
echo "  systemctl daemon-reload"
echo "  systemctl enable --now mailsub.timer"
