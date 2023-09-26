import adsk.core
import adsk.fusion

from .options import DogeboneFeatureInput

FACE = 'face'
INPUT = 'input'

GROUP_NAME = 'doge'


def saveToFeature(feature: adsk.fusion.BaseFeature, inputs: DogeboneFeatureInput, face: adsk.fusion.BRepFace):
    feature.attributes.add(GROUP_NAME, INPUT, inputs.asJson())
    feature.attributes.add(GROUP_NAME, FACE, face.entityToken)
