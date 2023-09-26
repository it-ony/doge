import adsk.core
import adsk.fusion

from .log import logger

# Keep track of all currently running commands in a global set, so their
# callback handlers are not garbage collected.
runningCommands = set()


def handler(handler_cls, callback):
    class ForwardingHandler(handler_cls):
        def __init__(self, _callback):
            super().__init__()
            self.callback = _callback

        def notify(self, args):
            try:
                self.callback(args)
            except Exception as e:
                logger.exception(e)
                raise e

    return ForwardingHandler(callback)


class RunningCommandBase(object):
    """
    Base class to keep persistent data during the lifetime of a command from
    creation to destruction. The constructor of this class automatically adds
    the instance to running_commands and the onDestroy event removes it again.
    To use this class, inherit from it an override the events.
    """

    def __init__(self, _args):
        runningCommands.add(self)

        self._inputChangedHandler = None
        self._selectionHandler = None
        self._validateHandler = None
        self._executeHandler = None
        self._executePreviewHandler = None
        self._destroyHandler = None

    # noinspection DuplicatedCode
    def onCreate(self, args):
        cmd = adsk.core.Command.cast(args.command)

        self._inputChangedHandler = handler(
            adsk.core.InputChangedEventHandler, self.onInputChanged)
        cmd.inputChanged.add(self._inputChangedHandler)

        self._selectionHandler = handler(
            adsk.core.SelectionEventHandler, self.onSelectionEvent)
        # noinspection PyUnresolvedReferences
        cmd.selectionEvent.add(self._selectionHandler)

        self._validateHandler = handler(
            adsk.core.ValidateInputsEventHandler, self.onValidate)
        cmd.validateInputs.add(self._validateHandler)

        self._executeHandler = handler(
            adsk.core.CommandEventHandler, self.onExecute)
        cmd.execute.add(self._executeHandler)

        self._executePreviewHandler = handler(
            adsk.core.CommandEventHandler, self.onExecutePreview)
        cmd.executePreview.add(self._executePreviewHandler)

        self._destroyHandler = handler(
            adsk.core.CommandEventHandler, self.onDestroy)
        cmd.destroy.add(self._destroyHandler)

    def onCreated(self, args):
        pass

    def onInputChanged(self, args):
        pass

    def onSelectionEvent(self, args):
        pass

    def onValidate(self, args):
        pass

    def onExecute(self, args):
        pass

    def onExecutePreview(self, args):
        pass

    def onDestroy(self, _args):
        runningCommands.remove(self)


class AddIn(object):
    # Defaults that are None have to be overridden in derived classes.
    COMMAND_ID = None
    FEATURE_NAME = None
    RESOURCE_FOLDER = None
    CREATE_TOOLTIP = ''
    EDIT_TOOLTIP = ''
    PANEL_NAME = None
    RUNNING_CREATE_COMMAND_CLASS = None

    def __init__(self):
        fusion = adsk.core.Application.get()
        self.fusionUI = fusion.userInterface

        # Add handler for creating the feature.
        self._createHandler = handler(
            adsk.core.CommandCreatedEventHandler, self._onCreate)

    def _onCreate(self, args):
        running_command = self.RUNNING_CREATE_COMMAND_CLASS(args)
        running_command.onCreate(args)

    def _getCreateButtonId(self):
        return self.COMMAND_ID + 'Create'

    def _getCreateButtonName(self):
        return self.FEATURE_NAME

    def addToUi(self):
        # If there are existing instances of the button, clean them up first.
        try:
            self.removeFromUI()
        except Exception as e:
            logger.exception(e)
            pass

        # Create a command for creating the feature.
        createCommandDefinition = self.fusionUI.commandDefinitions.addButtonDefinition(
            self._getCreateButtonId(), self._getCreateButtonName(), self.CREATE_TOOLTIP, self.RESOURCE_FOLDER)
        createCommandDefinition.commandCreated.add(self._createHandler)

        # Add a button to the UI.
        panel = self.fusionUI.allToolbarPanels.itemById(self.PANEL_NAME)
        buttonControl = panel.controls.addCommand(createCommandDefinition)
        buttonControl.isPromotedByDefault = True
        buttonControl.isPromoted = True

    def removeFromUI(self):
        createCommandDefinition = self.fusionUI.commandDefinitions.itemById(self._getCreateButtonId())
        if createCommandDefinition:
            createCommandDefinition.deleteMe()

        panel = self.fusionUI.allToolbarPanels.itemById(self.PANEL_NAME)
        buttonControl = panel.controls.itemById(self._getCreateButtonId())
        if buttonControl:
            buttonControl.deleteMe()
