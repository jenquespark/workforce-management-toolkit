"""Entry point for the Workforce Management Toolkit package.

Running ``python -m wfm_toolkit`` launches the small CLI (same surface as the
installed ``wfm-toolkit`` console script).
"""

from .cli import main

if __name__ == "__main__":
    main()
