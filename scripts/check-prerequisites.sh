#!/usr/bin/env bash
set -euo pipefail

missing=0
for command in git docker; do
  if command -v "$command" >/dev/null 2>&1; then
    printf 'OK   %-10s %s\n' "$command" "$(command -v "$command")"
  else
    printf 'MISS %-10s not found\n' "$command"
    missing=1
  fi
done

if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    printf 'OK   %-10s %s\n' 'compose' "$(docker compose version --short 2>/dev/null || docker compose version)"
  else
    printf 'MISS %-10s Docker Compose plugin not available\n' 'compose'
    missing=1
  fi
  if docker info >/dev/null 2>&1; then
    printf 'OK   %-10s daemon reachable\n' 'docker-daemon'
  else
    printf 'WARN %-10s daemon unavailable; start Docker Desktop or the WSL Docker service\n' 'docker-daemon'
  fi
fi

exit "$missing"
