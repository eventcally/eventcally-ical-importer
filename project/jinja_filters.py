import os

from project import app


def env_override(value, key):
    return os.getenv(key, value)


app.jinja_env.filters["env_override"] = env_override
