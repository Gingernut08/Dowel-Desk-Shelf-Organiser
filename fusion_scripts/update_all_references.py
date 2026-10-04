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
alreadyCurrent = []
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
                "in this folder or its subfolders"
            )
            
            return

        # Process every design
        for index, item in enumerate(allFiles, start = 1):
            dataFile = item[0]
            folderPath = item[1]
            
            print()
            print("=" * 70)
            
            print(f"[{index}/{len(allFiles)}] {dataFile.name}")
            
            if folderPath:
                print(f"Cloud path: {folderPath}")
            
            print("=" * 70)
            
            document = None
            
            try:
                # Check if the user has the file open
                if dataFile.isInUse:
                    print("SKIPPED - file is currently in use")
                    
                    skipped.append((dataFile.name, "File is currently in use"))
                    continue
                
                # Check if the file is read-only
                if dataFile.isReadOnly:
                    print("SKIPPED - file is read-only")
                    
                    skipped.append((dataFile.name, "File is read-only"))
                    continue
                
                # Open cloud design
                print("Opening cloud design")
                document = app.documents.open(dataFile)
                
                if document is None:
                    raise RuntimeError("Fusion failed to open the document")

                document.activate()
                
                # Convert to Fusion Document
                fusionDocument = (adsk.fusion.FusionDocument.cast(document))
                
                if fusionDocument is None:
                    raise RuntimeError("The opened document is not a Fusion Document")
                
                processed.append(dataFile.name)
                
                # Show references
                print_references(fusionDocument)
                
                # Check reference state
                print("Checking external references")
                upToDate = (fusionDocument.isUpToDate)
                
                if upToDate:
                    print("OK - all references are current")
                    
                    alreadyCurrent.append(dataFile.name)
                    continue
                
                # Out of date references
                print("OUT OF DATE - updating references")
                result = (fusionDocument.updateAllReferences())
                
                if not result:
                    raise RuntimeError("updateAllReferences returned False") 
                
                # Give Fusion processing time
                print("Waiting for Fusion to finish updating references")
                time.sleep(1)
                
                # Verify the update
                if fusionDocument.isUpToDate:
                    print("References updated successfully")
                else:
                    print("WARNING: Fusion reports out-of-date references")
                
                # Check if Fusion actually modified the document
                if not fusionDocument.isModified:
                    print("No document changes detected")
                    
                    alreadyCurrent.append(dataFile.name)
                    continue
                
                # Save the updated design
                print("Saving updated Fusion version")
                
                saveResult = (fusionDocument.save(SAVE_DESCRIPTION))
                
                if not saveResult:
                    raise RuntimeError("Fusion failed to save the updated document")
                
                print("Saved successfully")
                updated.append(dataFile.name)
                
            except Exception as error:
                print()
                print("FAILED")
                print(str(error))
                
                failed.append((dataFile.name, folderPath, str(error)))
            
            # Close the document without another save
            if document is not None:
                try:
                    document.close(False)
                except Exception as closeError:
                    print(f"Could not close document: {str(closeError)}")
                    pass
        
        
        
        # FINAL SUMMARY
        summary = (
            "External referance update complete\n\n"
            f"Root folder:\n"
            f"{sourceFolder.name}\n\n"
            f"Fusion designs found: {len(allFiles)}\n"
            f"Processed: {len(processed)}\n"
            f"Updated and saved: {len(updated)}\n"
            f"Already current: {len(alreadyCurrent)}\n"
            f"Skipped: {len(skipped)}\n"
            f"Failed: {len(failed)}"
        )
        
        # Updated files
        if updated:
            summary += ("\n\nUpdated:")
            for filename in updated:
                sumary += ("\n + filename")
    except Exception:
        errorText = traceback.format_exc()
        
        print(errorText)
        
        if ui:
            ui.messageBox(f"Fatal error:\n\n{errorText}")