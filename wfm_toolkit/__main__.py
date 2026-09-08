"""Entry point for the Workforce Management Toolkit package.

Running ``python -m wfm_toolkit`` prints a short summary. There is no wired
Click CLI in this stage; the Python API is the primary interface.
"""

from .version import __version__


def main() -> None:
    """Print a short package summary."""
    print(f"Workforce Management Toolkit v{__version__}")
    print("Python API: from wfm_toolkit import ...")
    print("No CLI is wired in this stage; the Python API is the interface.")


if __name__ == "__main__":
    main()
