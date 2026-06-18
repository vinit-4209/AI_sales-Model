import json
import os


def _get_streamlit_secrets():
    try:
        import streamlit as st
        try:
            return dict(st.secrets)
        except Exception:
            return {}
    except Exception:
        return {}


def get_groq_api_key(default=None):
    secrets = _get_streamlit_secrets()
    for key in ("GROQ_API_KEY", "groq_api_key"):
        value = secrets.get(key)
        if value:
            return value

    return os.getenv("GROQ_API_KEY", default)


def get_service_account_credentials(default=None):
    secrets = _get_streamlit_secrets()

    for key in ("gcp_service_account", "google_service_account"):
        value = secrets.get(key)
        if value:
            return value

    for key in ("gcp_service_account_json", "GOOGLE_SERVICE_ACCOUNT_JSON"):
        value = secrets.get(key)
        if value:
            if isinstance(value, str):
                return json.loads(value)
            return value

    env_value = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if env_value:
        return json.loads(env_value)

    return default
