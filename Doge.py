from typing import Optional, List, cast, Union

import adsk.core
import adsk.fusion

from .geometry import updateDogFeature
from .log import logger
from .commands import Action
from . import util
from . import commands
from . import options
from . import geometry
from . import ui

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

    def onDestroy(self, args: adsk.core.CommandEventArgs):
        super().onDestroy(args)
        if args.terminationReason == adsk.core.CommandTerminationReason.CompletedTerminationReason:
            self.lastUsedInputs.writeDefaults()


class UpdateDogeCommand(commands.RunningCommandBase):

    def onExecute(self, args):
        app = adsk.core.Application.get()
        design: adsk.fusion.Design = cast(adsk.fusion.Design, app.activeProduct)

        def processFeature(obj: adsk.fusion.TimelineObject):

            if obj.entity.classType() == adsk.fusion.BaseFeature.classType():
                feature = cast(adsk.fusion.BaseFeature, obj.entity)
                updateDogFeature(feature, obj)

        def processTimeline(timeline: Union[adsk.fusion.Timeline, adsk.fusion.TimelineGroup]):
            for obj in timeline:
                if obj.isGroup:
                    group = cast(adsk.fusion.TimelineGroup, obj)
                    isCollapsed = group.isCollapsed
                    group.isCollapsed = False
                    processTimeline(group)
                    group.isCollapsed = isCollapsed
                else:
                    processFeature(obj)

        position = design.timeline.markerPosition
        try:
            processTimeline(design.timeline)
        finally:
            design.timeline.markerPosition = position

        # logger.warning(feature.name)


class DogeAddIn(commands.AddIn):
    def _prefix(self) -> str:
        return 'tfDoge'

    def actions(self) -> List[Action]:
        return [
            Action('create', 'Create Dogbone', 'Creates dogbones for given faces', 'resources/ui/create_button', CreateDogeCommand),
            Action('update', 'Update Dogbones', 'Update all dogbones', 'resources/ui/update_button', UpdateDogeCommand)
        ]


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
