import os

from project import app
from project.vite import vite_entry


def env_override(value, key):
    return os.getenv(key, value)


app.jinja_env.filters["env_override"] = env_override
app.jinja_env.globals["vite_entry"] = vite_entry
