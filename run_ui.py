"""
Launch the VaccineGenics Streamlit dashboard.

Usage:
  python run_ui.py
  streamlit run run_ui.py
"""
import sys
import os

# Expose Streamlit Cloud secrets as environment variables.
# Must run BEFORE src/ is added to path (config.py calls load_dotenv on import).
# Locally, .env is used instead. On Streamlit Cloud, secrets come from the dashboard.
try:
    import streamlit as st
    for _k, _v in st.secrets.items():
        if isinstance(_v, str):
            os.environ.setdefault(_k, _v)
except Exception:
    pass

# Ensure src/ is importable when running via `python run_ui.py` without pip install -e .
_src = os.path.join(os.path.dirname(__file__), "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from ui.app import main

if __name__ == "__main__":
    main()
