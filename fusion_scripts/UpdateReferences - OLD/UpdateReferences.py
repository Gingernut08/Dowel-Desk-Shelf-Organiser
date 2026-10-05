import adsk.core
import adsk.fusion
import traceback
import time


# ================================================================================ #
# CONFIG
# ================================================================================ #

SAVE_DESCRIPTION = "Updated external references by script"

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

def get_files(folder, path=""):

    files = []

    # Get all files in current folder
    for dataFile in folder.dataFiles:

        if dataFile.fileExtension.lower() == "f3d":

            files.append(
                (dataFile, path)
            )

    # Search each subfolder
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


# ================================================================================ #
# OUTPUT REFERENCES
# ================================================================================ #

def print_references(fusionDocument):

    try:

        references = (
            fusionDocument.allDocumentReferences
        )

        count = references.count

        print(
            f"EXTERNAL/reference documents: {count}"
        )

        if SHOW_REFERENCES:

            for i in range(count):

                # IMPORTANT:
                # Fusion collections use item(), not items()
                reference = references.item(i)

                if reference:

                    try:

                        print(
                            f"    - {reference.name}"
                        )

                    except:

                        pass

    except Exception as error:

        print(
            f"Could not read references: {str(error)}"
        )


# ================================================================================ #
# MAIN
# ================================================================================ #

def run(context):

    app = None
    ui = None

    try:

        app = adsk.core.Application.get()
        ui = app.userInterface

        # ------------------------------------------------------------------------
        # Get active cloud folder
        # ------------------------------------------------------------------------

        sourceFolder = app.data.activeFolder

        if sourceFolder is None:

            ui.messageBox(
                "Could not determine the active Fusion cloud folder"
            )

            return

        print("=" * 70)
        print(
            f"Root folder: {sourceFolder.name}"
        )

        # ------------------------------------------------------------------------
        # Find Fusion designs recursively
        # ------------------------------------------------------------------------

        print()
        print(
            "Searching folder and subfolders for design files"
        )

        allFiles = get_files(
            sourceFolder
        )

        # Sort by cloud folder + filename
        allFiles.sort(
            key=lambda item:
            f"{item[1]}/{item[0].name}".lower()
        )

        print(
            f"Found {len(allFiles)} Fusion design files"
        )

        if len(allFiles) == 0:

            ui.messageBox(
                "No .f3d Fusion designs were found "
                "in this folder or its subfolders"
            )

            return

        # ------------------------------------------------------------------------
        # Process every design
        # ------------------------------------------------------------------------

        for index, item in enumerate(
            allFiles,
            start=1
        ):

            dataFile = item[0]
            folderPath = item[1]

            print()
            print("=" * 70)

            print(
                f"[{index}/{len(allFiles)}] "
                f"{dataFile.name}"
            )

            if folderPath:

                print(
                    f"Cloud path: {folderPath}"
                )

            print("=" * 70)

            document = None

            try:

                # ----------------------------------------------------------------
                # Check if another user has the file open
                # ----------------------------------------------------------------

                if dataFile.isInUse:

                    print(
                        "SKIPPED - file is currently in use"
                    )

                    skipped.append(
                        (
                            dataFile.name,
                            "File is currently in use"
                        )
                    )

                    continue

                # ----------------------------------------------------------------
                # Check if file is read-only
                # ----------------------------------------------------------------

                if dataFile.isReadOnly:

                    print(
                        "SKIPPED - file is read-only"
                    )

                    skipped.append(
                        (
                            dataFile.name,
                            "File is read-only"
                        )
                    )

                    continue

                # ----------------------------------------------------------------
                # Open cloud design
                # ----------------------------------------------------------------

                print(
                    "Opening cloud design..."
                )

                document = app.documents.open(
                    dataFile
                )

                if document is None:

                    raise RuntimeError(
                        "Fusion failed to open the document"
                    )

                document.activate()

                # ----------------------------------------------------------------
                # Convert to FusionDocument
                # ----------------------------------------------------------------

                fusionDocument = (
                    adsk.fusion.FusionDocument.cast(
                        document
                    )
                )

                if fusionDocument is None:

                    raise RuntimeError(
                        "The opened document is not "
                        "a Fusion Document"
                    )

                processed.append(
                    dataFile.name
                )

                # ----------------------------------------------------------------
                # Show references
                # ----------------------------------------------------------------

                print_references(
                    fusionDocument
                )

                # ----------------------------------------------------------------
                # Check reference state
                # ----------------------------------------------------------------

                print(
                    "Checking external references..."
                )

                upToDate = (
                    fusionDocument.isUpToDate
                )

                if upToDate:

                    print(
                        "OK - all references are current"
                    )

                    alreadyCurrent.append(
                        dataFile.name
                    )

                    continue

                # ----------------------------------------------------------------
                # References are out of date
                # ----------------------------------------------------------------

                print(
                    "OUT OF DATE - updating references..."
                )

                result = (
                    fusionDocument.updateAllReferences()
                )

                if not result:

                    raise RuntimeError(
                        "updateAllReferences() returned False"
                    )

                # ----------------------------------------------------------------
                # Give Fusion time to process
                # ----------------------------------------------------------------

                print(
                    "Waiting for Fusion to finish "
                    "updating references..."
                )

                time.sleep(1)

                # ----------------------------------------------------------------
                # Verify update
                # ----------------------------------------------------------------

                if fusionDocument.isUpToDate:

                    print(
                        "References updated successfully"
                    )

                else:

                    print(
                        "WARNING: Fusion still reports "
                        "out-of-date references"
                    )

                # ----------------------------------------------------------------
                # Check if document changed
                # ----------------------------------------------------------------

                if not fusionDocument.isModified:

                    print(
                        "No document changes detected"
                    )

                    alreadyCurrent.append(
                        dataFile.name
                    )

                    continue

                # ----------------------------------------------------------------
                # Save updated design
                # ----------------------------------------------------------------

                print(
                    "Saving updated Fusion version..."
                )

                saveResult = fusionDocument.save(
                    SAVE_DESCRIPTION
                )

                if not saveResult:

                    raise RuntimeError(
                        "Fusion failed to save "
                        "the updated document"
                    )

                print(
                    "Saved successfully"
                )

                updated.append(
                    dataFile.name
                )

            except Exception as error:

                print()
                print(
                    "FAILED"
                )

                print(
                    str(error)
                )

                failed.append(
                    (
                        dataFile.name,
                        folderPath,
                        str(error)
                    )
                )

            finally:

                # ----------------------------------------------------------------
                # Close document
                # ----------------------------------------------------------------

                if document is not None:

                    try:

                        document.close(
                            False
                        )

                    except Exception as closeError:

                        print(
                            f"Could not close document: "
                            f"{str(closeError)}"
                        )

        # =========================================================================
        # FINAL SUMMARY
        # =========================================================================

        summary = (
            "External reference update complete\n\n"
            f"Root folder:\n"
            f"{sourceFolder.name}\n\n"
            f"Fusion designs found: {len(allFiles)}\n"
            f"Processed: {len(processed)}\n"
            f"Updated and saved: {len(updated)}\n"
            f"Already current: {len(alreadyCurrent)}\n"
            f"Skipped: {len(skipped)}\n"
            f"Failed: {len(failed)}"
        )

        # ------------------------------------------------------------------------
        # Updated files
        # ------------------------------------------------------------------------

        if updated:

            summary += "\n\nUpdated:"

            for filename in updated:

                summary += (
                    f"\n  {filename}"
                )

        # ------------------------------------------------------------------------
        # Skipped files
        # ------------------------------------------------------------------------

        if skipped:

            summary += "\n\nSkipped:"

            for filename, reason in skipped:

                summary += (
                    f"\n  {filename} - {reason}"
                )

        # ------------------------------------------------------------------------
        # Failed files
        # ------------------------------------------------------------------------

        if failed:

            summary += "\n\nFailed:"

            for filename, folder, error in failed:

                summary += (
                    f"\n\n  {filename}"
                )

                if folder:

                    summary += (
                        f"\n  Folder: {folder}"
                    )

                summary += (
                    f"\n  Error: {error}"
                )

        # ------------------------------------------------------------------------
        # Print final result
        # ------------------------------------------------------------------------

        print()
        print("=" * 70)
        print("COMPLETE")
        print("=" * 70)
        print(summary)

        ui.messageBox(
            summary
        )

    except Exception:

        errorText = traceback.format_exc()

        print(
            errorText
        )

        if ui:

            ui.messageBox(
                f"Fatal error:\n\n{errorText}"
            )