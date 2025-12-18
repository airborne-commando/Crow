import sys
import os
import tkinter as tk

# Add the modular directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
modular_dir = os.path.join(current_dir, "modular-filters")
sys.path.insert(0, modular_dir)

# Import from modular directory
try:
    from gui import BlackbirdFilterGeneratorGUI
    print("Successfully imported modules from modular-filters/ directory")
except ImportError as e:
    print(f"Error importing from modular-filters directory: {e}")
    print("Trying to import individual modules...")
    
    # Try importing individual modules
    try:
        from modular.gui import BlackbirdFilterGeneratorGUI
    except ImportError:
        # If modular is a package, try relative import
        import importlib
        spec = importlib.util.spec_from_file_location(
            "gui", 
            os.path.join(modular_dir, "gui.py")
        )
        gui_module = importlib.util.module_from_spec(spec)
        sys.modules["gui"] = gui_module
        spec.loader.exec_module(gui_module)
        BlackbirdFilterGeneratorGUI = gui_module.BlackbirdFilterGeneratorGUI

def main():
    root = tk.Tk()
    app = BlackbirdFilterGeneratorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()