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

refinementDict = {
    "MeshRefinementLow": adsk.fusion.MeshRefinementSettings.MeshRefinementLow,
    "MeshRefinementMedium": adsk.fusion.MeshRefinementSettings.MeshRefinementMedium,
    "MeshRefinementHigh": adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
}

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

foundFiles = []

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

        # 3MF EXPORT
        if EXPORT_3MF:
            print("Exporting 3MF")
            
            threeMFFilename = (baseName + ".3mf")
            threeMFPath = get_unique_path(saveFolder, threeMFFilename)
            
            threeMFOptions = (exportManager.createC3MFExportOptions(rootComponant, threeMFPath))
            
            if threeMFOptions is None:
                raise RuntimeError("Could not create 3MF export options")
            
            # Set mesh refinement
            try:
                threeMFOptions.meshRefinement = (refinementDict[MESH_REFINEMENT])
            except Exception as meshError:
                print("Could not set mesh refinement")
                print(str(meshError))
            
            # Export one 3MF containing the entire design
            threeMFOptions.isOneFilePerBody = False
            
            # Don't send the file to a print utility
            threeMFOptions.sendToPrintUtility = False
            
            threeMFResult = (exportManager.execute(threeMFOptions))
            
            if not threeMFResult:
                raise RuntimeError("3MF export failed")
            
            threeMFExported.append((dataFile.name, threeMFPath))
            
            # Successfully processed
            processed.append(dataFile.name)
            
            print("EXPORT COMPLETE")
    except Exception as error:
        print()
        print("EXPORT FAILED")
        print(str(error))
        failed.append((dataFile.name, folderPath, str(error)))
    finally:
        # Close document
        if document is not None:
            try:
                document.close(False)
            except Exception as closeError:
                print("Could not close document:")
                print(str(closeError))


# ================================================================================
# EXPORT EVERYTHING
# ================================================================================

def export_all():
    global foundFiles, processed, stepExported, threeMFExported, skipped, failed
    
    foundFiles = []
    
    processed = []
    stepExported = []
    threeMFExported = []
    
    skipped = []
    failed = []
    
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get active Fusion cloud folder
        sourceFolder = (app.data.activeFolder)
        
        if sourceFolder is None:
            ui.messageBox("Could not determine the active Fusion cloud folder")
            return
        
        print()
        print("=" * 70)
        
        print("EXPORT ALL FUSION FILES")
        
        print("=" * 70)
        
        print(f"Source folder: {sourceFolder.name}")
        
        # Get local output folder
        saveFolder = get_output_folder()
        
        print(f"Save folder: {saveFolder}")
        
        # Find all F3D files
        print()
        print("Searching for .f3d files")
        
        foundFiles = get_files(sourceFolder)
        
        foundFiles.sort(key = lambda item: f"{item[0]}/{item[0].name}".lower())
        
        print(f"Found {len(foundFiles)} Fusion files")
        
        if len(foundFiles) == 0:
            ui.messageBox("No .f3d files were found in the active folder or subfolders")
            return
        
        # Export every file
        total = len(foundFiles)
        
        for index, item in enumerate(foundFiles, start = 1):
            dataFile = item[0]
            folderPath = item[1]
            
            export_file(dataFile, folderPath, saveFolder, index, total)
        
        # FINAL SUMMARY
        summary = (
                    "External reference update complete\n\n"
                    f"Source folder:\n"
                    f"{sourceFolder.name}\n\n"
                    f"F3D found: {len(foundFiles)}\n"
                    f"Successfully processed: {len(processed)}\n"
                    f"STEP files exported: {len(stepExported)}\n"
                    f"3MF files exported: {len(threeMFExported)}\n"
                    f"Skipped: {len(skipped)}\n"
                    f"Failed: {len(failed)}\n\n"
                    f"Save folder:\n"
                    f"{saveFolder}"
                )
        
        # Skipped
        if skipped:
            summary += "\n\nSkipped:"
            for filename, reason in skipped:
                summary += (f"\n {filename} - {reason}")
        
        # Failed
        if failed:
            summary += "\n\nFailed"
            for filename, folder, error in failed:
                summary += (f"\n {filename}")
                
                if folder:
                    summary += (f"\n Folder: {folder}")
                
                summary += (f"\n Error: {error}")
        
        print()
        print("=" * 70)
        print("COMPLETE")
        print("=" * 70)
        
        print(summary)
        
        ui.messageBox(summary)
        
    except Exception:
        errorText = traceback.format_exc()
        
        print(errorText)
        
        ui.messageBox(f"Fatal error:\n\n{errorText}")


# ================================================================================
# COMMAND CREATED HANDLER
# ================================================================================