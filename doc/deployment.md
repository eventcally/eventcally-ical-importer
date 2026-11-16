# Deployment

## Docker compose

[Docker compose](../deployment/docker-compose/README.md)

## Keys

Print environment variable EVENTCALLY_PRIVATE_KEY:

```sh
awk '{printf "%s\\n", $0}' private_key.pem
```

## Release

A release is a `vX.Y.Z` tag on `main`; pushing it builds and pushes the Docker image
(`docker-build-push-v2.yml`). Cut one with `scripts/release.sh` (or `/release` in Claude Code):

```sh
scripts/release.sh patch --dry-run   # checks, next version and generated notes
scripts/release.sh patch --watch     # create the release and follow the Docker build
```
