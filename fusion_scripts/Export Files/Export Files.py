import adsk.core
import adsk.fusion
import traceback
import time
import os


# ================================================================================
# CONFIG
# ================================================================================

# Leave empty to use:
# Downloads\Fusion Exports\<date and time>
SAVE_FOLDER = ""

EXPORT_STEP = True
EXPORT_3MF = True
EXPORT_OBJ = True

# Mesh quality:
# MeshRefinementLow
# MeshRefinementMedium
# MeshRefinementHigh
MESH_REFINEMENT = "MeshRefinementHigh"

refinementDict = {
    "MeshRefinementLow":
        adsk.fusion.MeshRefinementSettings.MeshRefinementLow,

    "MeshRefinementMedium":
        adsk.fusion.MeshRefinementSettings.MeshRefinementMedium,

    "MeshRefinementHigh":
        adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
}

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

COMMAND_NAME = "Export All STEP + 3MF + OBJ"

COMMAND_DESCRIPTION = (
    "Export every F3D in the active Fusion folder "
    "to STEP, 3MF and OBJ"
)


# ================================================================================
# FUSION UI LOCATION
# ================================================================================

WORKSPACE_ID = "FusionSolidEnvironment"

PANEL_ID = "SolidCreatePanel"


# ================================================================================
# RESULTS
# ================================================================================

foundFiles = []

processed = []

stepExported = []

threeMFExported = []

objExported = []

skipped = []

failed = []


# ================================================================================
# GET OUTPUT FOLDER
# ================================================================================

def get_output_folder():

    if SAVE_FOLDER:

        saveFolder = os.path.expandvars(
            os.path.expanduser(
                SAVE_FOLDER
            )
        )

    else:

        downloadsFolder = os.path.join(
            os.path.expanduser("~"),
            "Downloads"
        )

        saveFolder = os.path.join(
            downloadsFolder,
            "Fusion Exports",
            time.strftime(
                "%d-%m-%y_%H-%M-%S"
            )
        )

    os.makedirs(
        saveFolder,
        exist_ok=True
    )

    return saveFolder


# ================================================================================
# FIND ALL F3D FILES
# ================================================================================

def get_files(folder, path=""):

    files = []

    # --------------------------------------------------------------------------
    # Files in current folder
    # --------------------------------------------------------------------------

    for dataFile in folder.dataFiles:

        try:

            if dataFile.fileExtension.lower() == "f3d":

                files.append(
                    (
                        dataFile,
                        path
                    )
                )

        except Exception:

            pass


    # --------------------------------------------------------------------------
    # Search subfolders
    # --------------------------------------------------------------------------

    for subfolder in folder.dataFolders:

        if path:

            subfolderPath = (
                path
                + "/"
                + subfolder.name
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
# WINDOWS-SAFE FILENAME
# ================================================================================

def safe_filename(filename):

    invalid = '<>:"/\\|?* '

    for character in invalid:

        filename = filename.replace(
            character,
            "_"
        )

    return filename.strip()


# ================================================================================
# GET UNIQUE FILE PATH
# ================================================================================

def get_unique_path(folder, filename):

    path = os.path.join(
        folder,
        filename
    )

    if not os.path.exists(path):

        return path


    base, extension = os.path.splitext(
        filename
    )

    counter = 2

    while True:

        newFilename = (
            f"{base}_{counter}{extension}"
        )

        newPath = os.path.join(
            folder,
            newFilename
        )

        if not os.path.exists(newPath):

            return newPath

        counter += 1


# ================================================================================
# EXPORT ONE FILE
# ================================================================================

def export_file(
    dataFile,
    folderPath,
    saveFolder,
    index,
    total
):

    document = None

    print()
    print("=" * 70)

    print(
        f"[{index}/{total}] {dataFile.name}"
    )

    if folderPath:

        print(
            f"Fusion folder: {folderPath}"
        )

    print("=" * 70)


    try:

        # ----------------------------------------------------------------------
        # CHECK FILE
        # ----------------------------------------------------------------------

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

            return


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

            return


        # ----------------------------------------------------------------------
        # OPEN DESIGN
        # ----------------------------------------------------------------------

        print(
            "Opening Fusion design"
        )

        document = _app.documents.open(
            dataFile
        )

        if document is None:

            raise RuntimeError(
                "Fusion failed to open the document"
            )

        document.activate()

        time.sleep(
            WAIT_TIME
        )


        # ----------------------------------------------------------------------
        # GET FUSION DOCUMENT
        # ----------------------------------------------------------------------

        fusionDocument = (
            adsk.fusion.FusionDocument.cast(
                document
            )
        )

        if fusionDocument is None:

            raise RuntimeError(
                "Opened file is not a Fusion document"
            )


        # ----------------------------------------------------------------------
        # GET DESIGN
        # ----------------------------------------------------------------------

        design = (
            adsk.fusion.Design.cast(
                document.products.itemByProductType(
                    "DesignProductType"
                )
            )
        )

        if design is None:

            design = (
                adsk.fusion.Design.cast(
                    _app.activeProduct
                )
            )

        if design is None:

            raise RuntimeError(
                "Could not get Fusion Design Product"
            )


        # ----------------------------------------------------------------------
        # ROOT COMPONENT
        # ----------------------------------------------------------------------

        rootComponent = design.rootComponent

        if rootComponent is None:

            raise RuntimeError(
                "Could not get root component"
            )


        # ----------------------------------------------------------------------
        # EXPORT MANAGER
        # ----------------------------------------------------------------------

        exportManager = design.exportManager

        if exportManager is None:

            raise RuntimeError(
                "Could not get Fusion ExportManager"
            )


        # ----------------------------------------------------------------------
        # BASE NAME
        # ----------------------------------------------------------------------

        baseName = os.path.splitext(
            dataFile.name
        )[0]

        baseName = safe_filename(
            baseName
        )


        # ======================================================================
        # STEP
        # ======================================================================

        if EXPORT_STEP:

            print(
                "Exporting STEP"
            )

            stepFilename = (
                baseName
                + ".step"
            )

            stepPath = get_unique_path(
                saveFolder,
                stepFilename
            )

            stepOptions = (
                exportManager.createSTEPExportOptions(
                    stepPath,
                    rootComponent
                )
            )

            if stepOptions is None:

                raise RuntimeError(
                    "Could not create STEP export options"
                )

            stepResult = (
                exportManager.execute(
                    stepOptions
                )
            )

            if not stepResult:

                raise RuntimeError(
                    "STEP export failed"
                )

            print(
                f"STEP exported:\n{stepPath}"
            )

            stepExported.append(
                (
                    dataFile.name,
                    stepPath
                )
            )


        # ======================================================================
        # 3MF
        # ======================================================================

        if EXPORT_3MF:

            print(
                "Exporting 3MF"
            )

            threeMFFilename = (
                baseName
                + ".3mf"
            )

            threeMFPath = get_unique_path(
                saveFolder,
                threeMFFilename
            )

            threeMFOptions = (
                exportManager.createC3MFExportOptions(
                    rootComponent,
                    threeMFPath
                )
            )

            if threeMFOptions is None:

                raise RuntimeError(
                    "Could not create 3MF export options"
                )


            # ------------------------------------------------------------------
            # MESH REFINEMENT
            # ------------------------------------------------------------------

            try:

                threeMFOptions.meshRefinement = (
                    refinementDict[
                        MESH_REFINEMENT
                    ]
                )

            except Exception as meshError:

                print(
                    "Could not set 3MF mesh refinement"
                )

                print(
                    str(meshError)
                )


            # One 3MF containing entire design
            threeMFOptions.isOneFilePerBody = False

            # Do not send to print utility
            threeMFOptions.sendToPrintUtility = False


            threeMFResult = (
                exportManager.execute(
                    threeMFOptions
                )
            )

            if not threeMFResult:

                raise RuntimeError(
                    "3MF export failed"
                )

            print(
                f"3MF exported:\n{threeMFPath}"
            )

            threeMFExported.append(
                (
                    dataFile.name,
                    threeMFPath
                )
            )


        # ======================================================================
        # OBJ
        # ======================================================================

        if EXPORT_OBJ:

            print(
                "Exporting OBJ"
            )

            objFilename = (
                baseName
                + ".obj"
            )

            objPath = get_unique_path(
                saveFolder,
                objFilename
            )

            objOptions = (
                exportManager.createOBJExportOptions(
                    rootComponent,
                    objPath
                )
            )

            if objOptions is None:

                raise RuntimeError(
                    "Could not create OBJ export options"
                )


            # ------------------------------------------------------------------
            # MESH REFINEMENT
            # ------------------------------------------------------------------

            try:

                objOptions.meshRefinement = (
                    refinementDict[
                        MESH_REFINEMENT
                    ]
                )

            except Exception as meshError:

                print(
                    "Could not set OBJ mesh refinement"
                )

                print(
                    str(meshError)
                )


            objResult = (
                exportManager.execute(
                    objOptions
                )
            )

            if not objResult:

                raise RuntimeError(
                    "OBJ export failed"
                )

            print(
                f"OBJ exported:\n{objPath}"
            )

            objExported.append(
                (
                    dataFile.name,
                    objPath
                )
            )


        # ----------------------------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------------------------

        processed.append(
            dataFile.name
        )

        print(
            "EXPORT COMPLETE"
        )


    except Exception as error:

        print()
        print(
            "EXPORT FAILED"
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

        # ----------------------------------------------------------------------
        # CLOSE DOCUMENT
        # ----------------------------------------------------------------------

        if document is not None:

            try:

                document.close(
                    False
                )

            except Exception as closeError:

                print(
                    "Could not close document:"
                )

                print(
                    str(closeError)
                )


# ================================================================================
# EXPORT EVERYTHING
# ================================================================================

def export_all():

    global foundFiles
    global processed
    global stepExported
    global threeMFExported
    global objExported
    global skipped
    global failed


    # --------------------------------------------------------------------------
    # RESET RESULTS
    # --------------------------------------------------------------------------

    foundFiles = []

    processed = []

    stepExported = []

    threeMFExported = []

    objExported = []

    skipped = []

    failed = []


    try:

        app = adsk.core.Application.get()

        ui = app.userInterface


        # ----------------------------------------------------------------------
        # ACTIVE FUSION FOLDER
        # ----------------------------------------------------------------------

        sourceFolder = app.data.activeFolder

        if sourceFolder is None:

            ui.messageBox(
                "Could not determine the active Fusion cloud folder"
            )

            return


        print()
        print("=" * 70)

        print(
            "EXPORT ALL FUSION FILES"
        )

        print("=" * 70)

        print(
            f"Source folder: {sourceFolder.name}"
        )


        # ----------------------------------------------------------------------
        # OUTPUT FOLDER
        # ----------------------------------------------------------------------

        saveFolder = get_output_folder()

        print(
            f"Save folder: {saveFolder}"
        )


        # ----------------------------------------------------------------------
        # FIND FILES
        # ----------------------------------------------------------------------

        print()

        print(
            "Searching for .f3d files"
        )

        foundFiles = get_files(
            sourceFolder
        )


        # ----------------------------------------------------------------------
        # SORT
        # ----------------------------------------------------------------------

        foundFiles.sort(
            key=lambda item:
                f"{item[1]}/{item[0].name}".lower()
        )


        print(
            f"Found {len(foundFiles)} Fusion files"
        )


        if len(foundFiles) == 0:

            ui.messageBox(
                "No .f3d files were found in the active folder or subfolders"
            )

            return


        # ----------------------------------------------------------------------
        # EXPORT FILES
        # ----------------------------------------------------------------------

        total = len(
            foundFiles
        )

        for index, item in enumerate(
            foundFiles,
            start=1
        ):

            dataFile = item[0]

            folderPath = item[1]

            export_file(
                dataFile,
                folderPath,
                saveFolder,
                index,
                total
            )


        # ======================================================================
        # SUMMARY
        # ======================================================================

        summary = (
            "Export complete\n\n"

            f"Source folder:\n"
            f"{sourceFolder.name}\n\n"

            f"F3D found: "
            f"{len(foundFiles)}\n"

            f"Successfully processed: "
            f"{len(processed)}\n"

            f"STEP files exported: "
            f"{len(stepExported)}\n"

            f"3MF files exported: "
            f"{len(threeMFExported)}\n"

            f"OBJ files exported: "
            f"{len(objExported)}\n"

            f"Skipped: "
            f"{len(skipped)}\n"

            f"Failed: "
            f"{len(failed)}\n\n"

            f"Save folder:\n"
            f"{saveFolder}"
        )


        # ----------------------------------------------------------------------
        # SKIPPED
        # ----------------------------------------------------------------------

        if skipped:

            summary += (
                "\n\nSkipped:"
            )

            for filename, reason in skipped:

                summary += (
                    f"\n {filename} - {reason}"
                )


        # ----------------------------------------------------------------------
        # FAILED
        # ----------------------------------------------------------------------

        if failed:

            summary += (
                "\n\nFailed:"
            )

            for filename, folder, error in failed:

                summary += (
                    f"\n {filename}"
                )

                if folder:

                    summary += (
                        f"\n Folder: {folder}"
                    )

                summary += (
                    f"\n Error: {error}"
                )


        # ----------------------------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------------------------

        print()
        print("=" * 70)

        print(
            "COMPLETE"
        )

        print("=" * 70)

        print(
            summary
        )

        ui.messageBox(
            summary
        )


    except Exception:

        errorText = traceback.format_exc()

        print(
            errorText
        )

        ui.messageBox(
            f"Fatal error:\n\n{errorText}"
        )


# ================================================================================
# COMMAND CREATED HANDLER
# ================================================================================

class ExportCommandCreatedHandler(
    adsk.core.CommandCreatedEventHandler
):

    def __init__(self):

        super().__init__()


    def notify(self, args):

        try:

            eventArgs = (
                adsk.core.CommandCreatedEventArgs.cast(
                    args
                )
            )

            command = eventArgs.command

            executeHandler = (
                ExportExecuteHandler()
            )

            command.execute.add(
                executeHandler
            )

            _handlers.append(
                executeHandler
            )


        except:

            print(
                traceback.format_exc()
            )


# ================================================================================
# COMMAND EXECUTE HANDLER
# ================================================================================

class ExportExecuteHandler(
    adsk.core.CommandEventHandler
):

    def __init__(self):

        super().__init__()


    def notify(self, args):

        try:

            export_all()

        except:

            errorText = traceback.format_exc()

            print(
                errorText
            )

            if _ui:

                _ui.messageBox(
                    f"Export failed:\n\n{errorText}"
                )


# ================================================================================
# START ADD-IN
# ================================================================================

def run(context):

    global _app
    global _ui

    try:

        # ----------------------------------------------------------------------
        # APPLICATION
        # ----------------------------------------------------------------------

        _app = adsk.core.Application.get()

        if _app is None:

            raise RuntimeError(
                "Could not get Fusion Application"
            )


        # ----------------------------------------------------------------------
        # USER INTERFACE
        # ----------------------------------------------------------------------

        _ui = _app.userInterface

        if _ui is None:

            raise RuntimeError(
                "Could not get Fusion User Interface"
            )


        # ======================================================================
        # COMMAND DEFINITION
        # ======================================================================

        commandDefinitions = (
            _ui.commandDefinitions
        )


        # Remove old command
        oldCommand = (
            commandDefinitions.itemById(
                COMMAND_ID
            )
        )

        if oldCommand:

            oldCommand.deleteMe()


        # Create new command
        commandDefinition = (
            commandDefinitions.addButtonDefinition(
                COMMAND_ID,
                COMMAND_NAME,
                COMMAND_DESCRIPTION
            )
        )

        if commandDefinition is None:

            raise RuntimeError(
                "Could not create command definition"
            )


        # ======================================================================
        # COMMAND CREATED EVENT
        # ======================================================================

        createdHandler = (
            ExportCommandCreatedHandler()
        )

        commandDefinition.commandCreated.add(
            createdHandler
        )

        _handlers.append(
            createdHandler
        )


        # ======================================================================
        # DESIGN WORKSPACE
        # ======================================================================

        workspace = (
            _ui.workspaces.itemById(
                WORKSPACE_ID
            )
        )

        if workspace is None:

            raise RuntimeError(
                "Could not find Design workspace"
            )


        # ======================================================================
        # SOLID CREATE PANEL
        # ======================================================================

        panel = (
            workspace.toolbarPanels.itemById(
                PANEL_ID
            )
        )

        if panel is None:

            raise RuntimeError(
                "Could not find Solid Create panel"
            )


        # ======================================================================
        # REMOVE OLD CONTROL
        # ======================================================================

        existingControl = (
            panel.controls.itemById(
                COMMAND_ID
            )
        )

        if existingControl:

            existingControl.deleteMe()


        # ======================================================================
        # ADD COMMAND TO SOLID CREATE
        # ======================================================================

        control = (
            panel.controls.addCommand(
                commandDefinition
            )
        )

        if control is None:

            raise RuntimeError(
                "Could not add command to Solid Create panel"
            )


        # ======================================================================
        # PROMOTE TO MAIN TOOLBAR
        # ======================================================================

        control.isPromotedByDefault = True

        control.isPromoted = True


        # ======================================================================
        # SUCCESS
        # ======================================================================

        print()
        print("=" * 70)

        print(
            "EXPORT ADD-IN LOADED"
        )

        print(
            "Location: Design > Solid > Create"
        )

        print(
            "Button promoted to toolbar"
        )

        print("=" * 70)


    except Exception:

        errorText = traceback.format_exc()

        print(
            errorText
        )

        if _ui:

            _ui.messageBox(
                "Failed to start add-in:\n\n"
                + errorText
            )


# ================================================================================
# STOP ADD-IN
# ================================================================================

def stop(context):

    try:

        if _ui is None:

            return


        # ======================================================================
        # DESIGN WORKSPACE
        # ======================================================================

        workspace = (
            _ui.workspaces.itemById(
                WORKSPACE_ID
            )
        )

        if workspace:

            # ------------------------------------------------------------------
            # SOLID CREATE PANEL
            # ------------------------------------------------------------------

            panel = (
                workspace.toolbarPanels.itemById(
                    PANEL_ID
                )
            )

            if panel:

                control = (
                    panel.controls.itemById(
                        COMMAND_ID
                    )
                )

                if control:

                    control.deleteMe()


        # ======================================================================
        # COMMAND DEFINITION
        # ======================================================================

        commandDefinitions = (
            _ui.commandDefinitions
        )

        commandDefinition = (
            commandDefinitions.itemById(
                COMMAND_ID
            )
        )

        if commandDefinition:

            commandDefinition.deleteMe()


        print(
            "Export All STEP + 3MF + OBJ add-in stopped"
        )


    except:

        print(
            traceback.format_exc()
        )