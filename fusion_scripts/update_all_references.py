import adsk.core, adsk.fusion, traceback, time, os
# ================================================================================ #
# CONFIG
# ================================================================================ #

# Save message for each fusion save
SAVE_DESCRIPTION = "Updated external references by script"

# True for extra reference info
SHOW_REFERENCES = True


# ================================================================================ #
# RESULTS
# ================================================================================ #

processed = []
updated = []
already_current = []
skipped = []
failed = []


# ================================================================================ #
# FIND ALL DESIGNS
# ================================================================================ #

def get_files(folder, path = ""):
    files = []

    # Get all files in current folder
    for dataFile in folder.dataFiles:
        if dataFile.fileExtension.lower() == "f3d":
            files.append((dataFile, path))

    # Seach each subfolder
    for subfolder in folder.dataFolders:
        subfolderPath = (
            os.join(path, subfolder.name)
            if path
            else subfolder.name
        )

        files.extend(
            get_files(subfolder, subfolderPath)
        )

    return files


# ================================================================================ #
# OUTPUT REFERENCES
# ================================================================================ #

def print_references(fusionDocument):
    try:
        references = (
            fusionDocument.allDocumentReferences
        )
        count = references.count
        print(f"EXTERNAL/reference documents: {count}")

        if SHOW_REFERENCES:
            for i in range(count):
                reference = references.items(i)
                if reference:
                    try: 
                        print(f"    - {reference.name}")
                    except:
                        pass
    except Exception as error:
        print(f"Could not read references: {str(error)}")


# ================================================================================ #
# MAIN
# ================================================================================ #

def run(context):
    app = None
    ui = None
    
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        
        # Get active cloud folder
        sourceFolder = app.data.activeFolder
        if sourceFolder is None:
            ui.messageBox("Could not determine the active Fusion cloud folder")
            return
        print("=" * 70)
        print(f"Root folder: {sourceFolder.name}")
        
        # Find Fusion designs recursively
        print()
        print("Searching folder and subfolders for design files")
        allFiles = get_files(sourceFolder)
        
        # Sort by folder/home for predictable processing
        allFiles.sort(key = lambda item:(f"{item[1]}/{item[0].name}").lower())
        print(f"Found {len(allFiles)} Fusion design files")
        
        if len(allFiles) == 0:
            ui.messageBox(
                "No .f3d Fusion designs were found "
                "in this folder or its subfolders."
            )
            
            return

        # Process every design
    except:
        pass