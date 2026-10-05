import adsk.core
import adsk.fusion
import traceback
import time
import os


# ================================================================================
# CONFIG
# ================================================================================

# Local save folder
SAVE_FOLDER = ""

EXPORT_STEP = True
EXPORT_3MF = True

# 3mf quality MeshRefinementLow, MeshRefinementMedium, MeshRefinementHigh
MESH_REFINEMENT = "MeshRefinementHigh"

# Wait after opening document
WAIT_TIME = 1.0


# ================================================================================
# GLOBALS
# ================================================================================

_app = None
_ui = None

_handlers = []

# ================================================================================
# COMMAND SETTINGS
# ================================================================================

COMMAND_ID = "exportAllFusionFiles"
COMMAND_NAME = "Export All STEP + 3MF"

PANEL_ID = "ExportAllPanel"
PANEL_NAME = "Export"


# ================================================================================
# RESULTS
# ================================================================================

found_files = []

processed = []
stepExported = []
threeMFExported = []

skipped = []
failed = []


# ================================================================================
# GET OUTPUT FOLDER
# ================================================================================

def get_output_folder():
    # If custom folder has been configured, use it
    if SAVE_FOLDER:
        saveFolder = os.path.expandvars(os.path.expanduser(SAVE_FOLDER))
    
    else:
        # Default: Downloads\Fusion Exports
        downloadsFolder = os.path.join(os.path.expanduser("~"), "Downloads")
        saveFolder = os.path.join(downloadsFolder, "Fusion Exports")
    
    # Create folder if it doesn't exist
    os.makedirs(saveFolder, exist_ok=True)
