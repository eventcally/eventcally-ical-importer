# Deployment

## Docker compose

[Docker compose](../deployment/docker-compose/README.md)

## Keys

Print environment variable EVENTCALLY_PRIVATE_KEY:

```sh
awk '{printf "%s\\n", $0}' private_key.pem
```
