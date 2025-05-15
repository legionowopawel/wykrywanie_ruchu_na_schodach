# main.py
from diagnostics import run_diagnostic_tests
from ui import main as run_ui

def main():
    run_diagnostic_tests()
    run_ui()

if __name__ == "__main__":
    main()
