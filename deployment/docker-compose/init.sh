set -e
source .env

mkdir -p ${POSTGRES_DATA_PATH}
mkdir -p ${POSTGRES_BACKUP_PATH}
mkdir -p ${REDIS_DATA_PATH}
chown -R 1001 ${REDIS_DATA_PATH}
mkdir -p ${FLUENTD_LOG_PATH}
mkdir -p ${FLUENTD_CUSTOM_CONFIG_PATH}
cp ./fluentd-custom.config ${FLUENTD_CUSTOM_CONFIG_PATH}/fluentd-custom.config

echo "SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe())")"
echo "POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe())")"
echo "REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe())")"
