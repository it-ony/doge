# Author: Tony Findeisen
# Description: An Add-in for making dogebones
from typing import Optional

import adsk.core
import adsk.fusion


from .log import logger
from . import util
from . import commands
from . import options
from . import geometry
from . import ui

# from . import geometry

# Global variable to hold the add-in (created in run(), destroyed in stop())
addIn: Optional[commands.AddIn] = None


class CreateDogeCommand(commands.RunningCommandBase):

    def __init__(self, args: adsk.core.CommandCreatedEventArgs):
        super().__init__(args)

        defaults = options.DogeboneFeatureInput()
        self.ui = ui.DogeBoneUI(args.command.commandInputs, defaults)
        self.lastUsedInputs = defaults

    def onInputChanged(self, args: adsk.core.InputChangedEventArgs):
        self.ui.updateVisibility()
        self.ui.focusNextSelectionInput()

    def onValidate(self, args: adsk.core.ValidateInputsEventArgs):
        args.areInputsValid = self.ui.areInputsValid()

    def onExecutePreview(self, args: adsk.core.CommandEventArgs):
        pass
        # if self.ui.isPreviewEnabled():
        #     if self.doExecute():
        #         args.isValidResult = True
        #         self.ui.setInputErrorMessage('')
        #     else:
        #         self.ui.setInputErrorMessage('Finger joints could not be completed. Try selecting overlapping bodies and double-check the dimensions.')

    def onExecute(self, args: adsk.core.CommandEventArgs):
        # We split onExecute and doExecute here so we can re-use the main functionality in
        # onExecutePreview where we have to react differently to errors.
        try:
            self.doExecute()
        except Exception as e:
            logger.exception(e)
            args.executeFailed = True
            args.executeFailedMessage = 'Dogebones could not be completed'

    def doExecute(self):
        pass
        inputs = self.ui.createInputs()
        self.lastUsedInputs = inputs
        geometry.createDogeBones(inputs)

        # toolBodies = geometry.createToolBodies(inputs)
        # if toolBodies == True:
        #     # No cut is neccessary (bodies do not overlap).
        #     return True
        # elif toolBodies == False:
        #     # No cut is possible (e.g., because of invalid inputs).
        #     return False
        # else:
        #     self.createCustomFeature(inputs, *toolBodies)
        #     return True

    def onDestroy(self, args: adsk.core.CommandEventArgs):
        super().onDestroy(args)
        if args.terminationReason == adsk.core.CommandTerminationReason.CompletedTerminationReason:
            self.lastUsedInputs.writeDefaults()


class DogeAddIn(commands.AddIn):
    COMMAND_ID = 'tfDoge'
    FEATURE_NAME = 'Doge'
    RESOURCE_FOLDER = 'resources/ui/create_button'
    CREATE_TOOLTIP = 'Creates dogbones for given faces'
    EDIT_TOOLTIP = 'Edit dogbones'
    PANEL_NAME = 'SolidModifyPanel'
    RUNNING_CREATE_COMMAND_CLASS = CreateDogeCommand


def run(_context):
    global addIn
    try:
        if addIn is not None:
            stop({'IsApplicationClosing': False})
        addIn = DogeAddIn()
        addIn.addToUi()
    except Exception as e:
        logger.exception(e)
        util.reportError('Uncaught exception', True)


def stop(_context):
    global addIn

    if addIn:
        addIn.removeFromUI()

    addIn = None
