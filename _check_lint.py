"""Quick script to extract pyright diagnostics for our files."""
import subprocess, json, sys

result = subprocess.run(
    [sys.executable.replace("python.exe","").rstrip("\\") + "\\pyright.exe", "--outputjson"],
    capture_output=True, text=True, cwd=r"c:\Users\HP\OneDrive\Desktop\EV"
)

try:
    data = json.loads(result.stdout)
except:
    # Try stderr
    print("STDOUT:", result.stdout[:500])
    print("STDERR:", result.stderr[:500])
    sys.exit(1)

diags = data.get("generalDiagnostics", [])

our_files = ["utils\\whatif\\simulator.py", "utils\\whatif\\export.py", 
             "pages_app\\whatif_simulator.py", "components\\charts.py", 
             "components\\cards.py", "utils\\auth.py", "app.py",
             "pages_app\\home.py", "pages_app\\about.py", "pages_app\\dashboard.py",
             "pages_app\\login.py", "pages_app\\signup.py", "pages_app\\tutorial.py",
             "pages_app\\ai_agent.py", "pages_app\\settings_page.py", 
             "pages_app\\help_support.py", "utils\\mock_data.py"]

for d in diags:
    fpath = d["file"]
    for of in our_files:
        if of in fpath:
            line = d["range"]["start"]["line"] + 1
            sev = d["severity"]
            msg = d["message"][:150]
            fname = fpath.split("\\")[-1]
            parent = fpath.split("\\")[-2] if "\\" in fpath else ""
            print(f"{parent}/{fname}:{line} [{sev}] {msg}")
            break
