from typing import List

import adsk.core
import adsk.fusion
from abc import ABC, abstractmethod

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

    def __init__(self, args):
        runningCommands.add(self)
        self._command = adsk.core.Command.cast(args.command)

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


class Action(ABC):
    def __init__(self, id: str, buttonName: str, toolTip: str, resource: str, commandClass) -> None:
        super().__init__()
        self.id = id
        self.buttonName = buttonName
        self.toolTip = toolTip
        self.resource = resource
        self.commandClass = commandClass


def getCallbackForAction(action: Action):
    def callback(args):
        command_class: RunningCommandBase = action.commandClass(args)
        command_class.onCreate(args)

    return callback


class AddIn(ABC):
    # Defaults that are None have to be overridden in derived classes.
    PANEL_NAME = 'SolidModifyPanel'

    def __init__(self):
        fusion = adsk.core.Application.get()
        self.fusionUI = fusion.userInterface
        self._actions = self.actions()
        self.handler = []

    @abstractmethod
    def actions(self) -> List[Action]:
        pass

    @abstractmethod
    def _prefix(self) -> str:
        pass

    def addToUi(self):
        # If there are existing instances of the button, clean them up first.
        try:
            self.removeFromUI()
        except Exception as e:
            logger.exception(e)
            pass

        prefix = self._prefix()

        for action in self._actions:
            commandDefinition = self.fusionUI.commandDefinitions.addButtonDefinition(
                f"{prefix}_{action.id}", action.buttonName, action.toolTip, action.resource)

            h = handler(adsk.core.CommandCreatedEventHandler, getCallbackForAction(action))
            self.handler.append(h)
            commandDefinition.commandCreated.add(h)

            # Add a button to the UI.
            panel = self.fusionUI.allToolbarPanels.itemById(self.PANEL_NAME)
            buttonControl = panel.controls.addCommand(commandDefinition)
            buttonControl.isPromotedByDefault = True
            buttonControl.isPromoted = True

    def removeFromUI(self):

        prefix = self._prefix()

        for action in self._actions:
            buttonId = f"{prefix}_{action.id}"

            createCommandDefinition = self.fusionUI.commandDefinitions.itemById(buttonId)
            if createCommandDefinition:
                createCommandDefinition.deleteMe()

            panel = self.fusionUI.allToolbarPanels.itemById(self.PANEL_NAME)
            buttonControl = panel.controls.itemById(buttonId)
            if buttonControl:
                buttonControl.deleteMe()

        self.handler = []
