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
        saveFolder = os.path.join(downloadsFolder, "Fusion Exports", time.strftime("%d-%m-%y_%H:%M:%S"))
    
    # Create folder if it doesn't exist
    os.makedirs(saveFolder, exist_ok=True)

    return saveFolder


# ================================================================================
# FIND ALL F3D FILES
# ================================================================================

def get_files(folder, path=""):

    files = []

    # Get all files in current folder.
    for dataFile in folder.dataFiles:

        if dataFile.fileExtension.lower() == "f3d":

            files.append(
                (dataFile, path)
            )

    # Search subfolders recursively.
    for subfolder in folder.dataFolders:

        if path:

            subfolderPath = (
                path + "/" + subfolder.name
            )

        else:

            subfolderPath = subfolder.name

        files.extend(
            get_files(
                subfolder,
                subfolderPath
            )
        )

    return files


# ================================================================================
# MAKE WIDNOWS SAFE FILENAME
# ================================================================================

def safe_filename(filename):
    invalid = "<>:\"/\\|?* "
    for character in invalid:
        filename.replace(character, "_")
    return filename.strip()


# ================================================================================
# GET UNIQUE SAVE PATH
# ================================================================================

def get_unique_path(folder, filename):
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return path
    
    base, extension = os.path.splitext(filename)
    
    counter = 2
    
    while True:
        newFilename = (f"{base}_{counter}{extension}")
        newPath = os.path.join(folder, newFilename)
        
        if not os.path.exists(newPath):
            return newPath
        
        counter += 1


# ================================================================================
# EXPORT ONE FILE
# ================================================================================

def export_file(dataFile, folderPath, saveFolder, index, total):
    document = None
    
    print()
    print("=" * 70)
    
    print(f"[{index}/{total}] {dataFile.name}")
    
    if folderPath:
        print(f"Fusion folder: {folderPath}")
    
    print("=" * 70)
    
    try:
        # Check if file in use
        if dataFile.isInUse:
            print("SKIPPED - file is currently in use")
        
            skipped.append((dataFile.name, "File is currently in use"))
            return
        
        # Check if file is read-only
        if dataFile.isReadOnly:
            print("SKIPPED - file is read-only")
        
            skipped.append((dataFile.name, "File is read-only"))
            return
        
        # Open design
        print("Opening Fusion design")
        
        document = _app.documents.open(dataFile)
        
        if document is None:
            raise RuntimeError("Fusion failed to open the document")
        
        document.activate()
        
        # Give Fusion time to open
        time.sleep(WAIT_TIME)
        
        # Get Fusion design
        
        fusionDocument = (adsk.fusion.FusionDocument.cast(document))
        
        if fusionDocument is None:
            raise RuntimeError("Opened file is not a Fusion document")
        
        design = (adsk.fusion.Design.cast(document.products.itemByProductType("DesignProductType")))
        
        if design is None:
            design = (adsk.fusion.Design.cast(_app.activeProduct))
        
        if design is None:
            raise RuntimeError("Could not get Fusion Design Product")
        
        # Get root componant
        rootComponant = (design.rootComponant)
        
        if rootComponant is None:
            raise RuntimeError("Could not get root componant")
        
        # Get ExportManager
        exportManager = (design.exportManager)
        
        if exportManager is None:
            raise RuntimeError("Could not get Fusion ExportManager")
        
        # Get base filename
        baseName = os.path.splitext(dataFile.name)[0]
        baseName = safe_filename(baseName)
        
        # STEP EXPORT
        if EXPORT_STEP:
            print("Exporting STEP")
            
            stepFilename = (baseName + ".step")
            stepPath = get_unique_path(saveFolder, stepFilename)
            
            stepOptions = (exportManager.createSTEPExportOptions(stepPath, rootComponant))
            
            if stepOptions is None:
                raise RuntimeError("Could not create STEP export options")
            
            stepResult = (exportManager.execute(stepOptions))
            
            if not stepResult:
                raise RuntimeError("STEP export failed")
            
            print(f"STEP exported:\n{stepPath}")
            stepExported.append((dataFile.name, stepPath))
        if EXPORT_3MF:
            pass
    except:
        pass