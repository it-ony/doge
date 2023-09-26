from typing import cast

import adsk.core
import adsk.fusion

from .options import DogeboneFeatureInput, DogeboneType, FusionExpression


class Input:
    FACE_SELECT = 'faceSelect'
    DOGBONE_TYPE = 'dogeboneType'
    TOOL_DIAMETER = 'toolDiameter'

    NORMAL_DOGBONE = 'normal Dogbone'
    MINIMAL_DOGBONE = 'minimal Dogbone'
    MORTISE_DOGBONE = 'mortise Dogbone'


DogboneTypeFromIndex = [DogeboneType.NORMAL, DogeboneType.MINIMAL, DogeboneType.MORTISE]


class DogeBoneUI(object):

    def __init__(self, inputs: adsk.core.CommandInputs, defaults: DogeboneFeatureInput):
        app = adsk.core.Application.get()
        unitsManager = app.activeProduct.unitsManager
        defaultUnit = unitsManager.defaultLengthUnits

        self._inputs = inputs

        self._inputFaces = inputs.addSelectionInput(
            Input.FACE_SELECT, 'Face',
            'Select a face to apply dogbones to all internal corner edges')
        self._inputFaces.addSelectionFilter(adsk.core.SelectionCommandInput.PlanarFaces)
        self._inputFaces.setSelectionLimits(1, 0)

        defaultToolDiameter = adsk.core.ValueInput.createByString(defaults.toolDiameter.expression)
        self._inputToolDiameter = inputs.addValueInput(Input.TOOL_DIAMETER, "Tool Diameter", defaultUnit, defaultToolDiameter)

        self._inputType: adsk.core.ButtonRowCommandInput = inputs.addButtonRowCommandInput(Input.DOGBONE_TYPE, "Type", False)
        inputType = self._inputType
        self._inputTypeNormal = inputType.listItems.add(Input.NORMAL_DOGBONE, defaults.dogeboneType == DogeboneType.NORMAL, "resources/ui/type/normal")
        self._inputTypeMinimal = inputType.listItems.add(Input.MINIMAL_DOGBONE, defaults.dogeboneType == DogeboneType.MINIMAL, "resources/ui/type/minimal")
        self._inputTypeMortise = inputType.listItems.add(Input.MORTISE_DOGBONE, defaults.dogeboneType == DogeboneType.MORTISE, "resources/ui/type/hidden")
        inputType.tooltipDescription = (
            "Minimal dogbones creates visually less prominent dogbones, but results in an interference fit "
            "that, for example, will require a larger force to insert a tenon into a mortise.\n"
            "\nMortise dogbones create dogbones on the shortest sides, or the longest sides.\n"
            "A piece with a tenon can be used to hide them if they're not cut all the way through the workpiece."
        )

        self._inputErrorMessage = inputs.addTextBoxCommandInput('inputErrorMessage', '', '', 3, True)
        self._inputErrorMessage.isFullWidth = True

        self.updateVisibility()
        self.focusNextSelectionInput()

    def updateVisibility(self):
        pass

    def setInputErrorMessage(self, msg):
        # We guard this statement to prevent an infinite loop of setting
        # the value, validating the input because an input changed, computing
        # the preview because the validation was successfull, and setting the
        #  value to '' there.
        # Unfortunately, setting the formatted value to x doesn't mean that the
        # value is x afterwards  (e.g., '' is turned into '<br />').
        if msg:
            formattedText = '<p style="color:red">{}</p>'.format(msg)
            if self._inputErrorMessage.formattedText != formattedText:
                self._inputErrorMessage.formattedText = formattedText
        else:
            if self._inputErrorMessage.text != '':
                self._inputErrorMessage.text = ''

    def focusNextSelectionInput(self):
        for input in self._inputs:
            if isinstance(input, adsk.core.SelectionCommandInput) and input.selectionCount == 0:
                input.hasFocus = True
                break

    @staticmethod
    def _getDistanceExpression(input: adsk.core.ValueCommandInput) -> FusionExpression:
        if input.isVisible:
            expression = FusionExpression(input.expression)
            if expression.isValid:
                return expression

    def toolDiameter(self) -> FusionExpression:
        return self._getDistanceExpression(self._inputToolDiameter)

    def dogeboneType(self) -> str:
        return DogboneTypeFromIndex[self._inputType.selectedItem.index]

    def createInputs(self):
        inputs = DogeboneFeatureInput()
        inputs.dogeboneType = self.dogeboneType()
        inputs.toolDiameter = self.toolDiameter()

        faces = self._inputFaces
        inputs.faces = {
            cast(adsk.fusion.BRepFace, faces.selection(i).entity).entityToken: faces.selection(i).entity
            for i in range(faces.selectionCount)
        }

        return inputs

    def areInputsValid(self):
        valid = True
        errorMessage = ''

        if self.toolDiameter().value <= 0:
            errorMessage = 'tool diameter must be positive'
            valid = False

        self.setInputErrorMessage(errorMessage)
        return valid
