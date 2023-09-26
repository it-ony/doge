import json
import os
from typing import Dict

import adsk.core
import adsk.fusion

from . import util

from .log import logger

APP_PATH = os.path.dirname(os.path.abspath(__file__))


class DogeboneType:
    NORMAL = 'normal'
    MINIMAL = 'minimal'
    MORTISE = 'mortise'


class FusionExpression(object):
    def __init__(self, expression):
        self._expression = expression

    @property
    def expression(self):
        return self._expression

    @expression.setter
    def expression(self, value):
        self._expression = value

    @property
    def value(self):
        unitsManager = adsk.core.Application.get().activeProduct.unitsManager
        return unitsManager.evaluateExpression(self._expression)

    @property
    def isValid(self):
        unitsManager = adsk.core.Application.get().activeProduct.unitsManager
        return unitsManager.isValidExpression(self._expression, unitsManager.defaultLengthUnits)


# Fusion distinguishes three types of parameters:
#  (1) Entities (objects in the design) are saved as dependencies.
#  (2) Values (numerical parameters, booleans?) are saved as custom parameters.
#  (3) Settings (choices in select boxes) are saved as named values.
# We want to keep track of all of them and store default values for values and settings.
class DogeboneFeatureInput(object):
    DEFAULTS_FILENAME = os.path.join(APP_PATH, 'defaults.json')
    DEFAULTS_DATA = {}

    def __init__(self):
        # Entities
        self.faces: Dict[str, adsk.fusion.BRepFace] = {}
        # Settings
        self.dogeboneType = DogeboneType.NORMAL
        # Values
        self.toolDiameter = FusionExpression("3.175 mm")
        self.readDefaults()

    def writeDefaults(self):
        with open(self.DEFAULTS_FILENAME, 'w', encoding='UTF-8') as json_file:
            json.dump(self.data(), json_file, ensure_ascii=False)

    def data(self):
        return {
            'dogeboneType': self.dogeboneType,
            'toolDiameter': self.toolDiameter.expression
        }

    def asJson(self) -> str:
        return json.dumps(self.data())

    def readDefaults(self):
        def expressionOrDefault(value, default):
            expression = FusionExpression(value)
            if value and expression.isValid:
                return expression
            else:
                return default

        if not os.path.isfile(self.DEFAULTS_FILENAME):
            return
        with open(self.DEFAULTS_FILENAME, 'r', encoding='UTF-8') as json_file:
            try:
                data = json.load(json_file)
            except Exception as e:
                logger.exception(e)
                util.reportError('Cannot read default options. Invalid JSON in "%s":' % self.DEFAULTS_FILENAME)
                data = {}

        self.dogeboneType = data.get('dogeboneType', self.dogeboneType)
        self.toolDiameter = expressionOrDefault(data.get('toolDiameter'), self.toolDiameter)
