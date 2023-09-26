import math
from typing import cast, List, Union

from .feature import saveToFeature
from .log import logger
from .options import DogeboneFeatureInput

import adsk.core
import adsk.fusion

_app = adsk.core.Application.get()
_design: adsk.fusion.Design = cast(adsk.fusion.Design, _app.activeProduct)
_rootComp = _design.rootComponent


def getFaceNormal(face: adsk.fusion.BRepFace):
    return face.evaluator.getNormalAtPoint(face.pointOnFace)[1]


def native(obj: Union[adsk.fusion.BRepFace, adsk.fusion.BRepEdge]):
    return obj.nativeObject if obj.nativeObject else obj


def getEdgeVector(
    edge: adsk.fusion.BRepEdge, refFace: adsk.fusion.BRepFace = None, reverse=False
) -> adsk.core.Vector3D:
    """
    returns vector of the edge parameter (not normalised!)
    if refFace is supplied - returns vector pointing out from face vertex"""
    if refFace:
        reverse = edge.endVertex in refFace.vertices
    startPoint, endPoint = (
        (edge.endVertex.geometry, edge.startVertex.geometry)
        if reverse
        else (edge.startVertex.geometry, edge.endVertex.geometry)
    )
    return startPoint.vectorTo(endPoint)


def getAngleBetweenFaces(edge: adsk.fusion.BRepEdge) -> float:
    """
    returns radian angle between faces
    """

    """
    Steps:
    get both adjacent faces of the edge
    crossProduct of these face Normals will point up or down
    to determine which is up compare direction with edge
    but: the edge direction needs to be determined 
    outer coEdges always run counterClockwise
    get the coEdge for face1
    orient the edge vector so it is has the same direction as the coEdge.
    
    Then with edge vertical, face1 on left, face2 on right, coEdge1 will be up
    if inside corner: face1normal x face2normal result will be in DOWN direction
    ie opposite to face1 coEdge direction
    """
    # Verify that the two faces are planar.
    face1, face2 = (face for face in edge.faces)

    if not face1 or not face2:
        return 0

    if face1.geometry.objectType != adsk.core.Plane.classType() or face2.geometry.objectType != adsk.core.Plane.classType():
        return 0

    # Get the normal of each face.
    _, normal1 = face1.evaluator.getNormalAtPoint(face1.pointOnFace)
    _, normal2 = face2.evaluator.getNormalAtPoint(face2.pointOnFace)
    # Get the angle between the normals.
    normalAngle = normal1.angleTo(normal2)

    # Get the co-edge of the selected edge for face1.
    coEdge1, coEdge2 = (coEdge for coEdge in edge.coEdges)
    coEdge = coEdge1 if coEdge1.loop.face == face1 else coEdge2

    # Create a vector that represents the direction of the co-edge.
    edgeVec = getEdgeVector(edge, reverse=coEdge.isOpposedToEdge)

    # Get the cross product of the face normals.
    # normal1 and normal2 are flipped as edge vector is pointing "up"
    cross = normal2.crossProduct(normal1)

    # Check to see if the cross product is in the same or opposite direction
    # of the co-edge direction.  If it's opposed then it's a convex angle.
    angle = (
        (math.pi * 2) - (math.pi - normalAngle)
        if edgeVec.angleTo(cross) > math.pi / 2
        else math.pi - normalAngle
    )

    return angle


def getCornerVector(edge: adsk.fusion.BRepEdge) -> adsk.core.Vector3D:
    face1, face2 = (face for face in native(edge).faces)

    _, face1normal = face1.evaluator.getNormalAtPoint(face1.pointOnFace)
    _, face2normal = face2.evaluator.getNormalAtPoint(face2.pointOnFace)
    face1normal.add(face2normal)
    face1normal.normalize()

    return face1normal


def getToolBody(edge: adsk.fusion.BRepEdge, face: adsk.fusion.BRepFace, inputs: DogeboneFeatureInput, topFace: adsk.fusion.BRepFace = None):
    tempBrepMgr = adsk.fusion.TemporaryBRepManager.get()

    faceNative = native(face)
    edgeNative = native(edge)

    nativeEndPoints = (
        (edgeNative.startVertex.geometry, edgeNative.endVertex.geometry)
        if edgeNative.startVertex in faceNative.vertices
        else (edgeNative.endVertex.geometry, edgeNative.startVertex.geometry)
    )

    startPoint, endPoint = nativeEndPoints

    startPoint, endPoint = startPoint.copy(), endPoint.copy()

    # offset = params.toolDiaOffset
    # TODO: where does the offset come from
    offset = 0
    effectiveRadius = (inputs.toolDiameter.value + offset) / 2
    # centreDistance = effectiveRadius * (
    #     (1 + params.minimalPercent / 100)
    #     if params.dbType == "Minimal Dogbone"
    #     else 1
    # )
    centreDistance = effectiveRadius

    # if topFace:
    #     translateVector = dbUtils.getTranslateVectorBetweenFaces(
    #         edgeObj._parentFace.face, topFace
    #     )
    #     startPoint.translateBy(translateVector)

    dirVect = getCornerVector(edge).copy()
    dirVect.normalize()

    dirVect.scaleBy(centreDistance)
    startPoint.translateBy(dirVect)
    endPoint.translateBy(dirVect)

    toolBody = tempBrepMgr.createCylinderOrCone(
        endPoint, effectiveRadius, startPoint, effectiveRadius
    )

    cornerAngle = getAngleBetweenFaces(edge)
    if cornerAngle >= math.pi / 2:
        return toolBody

    # creating a box that will be used to clear the path the tool takes to the dogbone hole
    # box width is toolDia
    # box height is same as edge length
    # box length is from the hole centre to the point where the tool meets the sides

    raise Exception('Not implemented')
    # edgeHeight = startPoint.distanceTo(endPoint)
    #
    # logger.debug("Adding acute angle clearance box")
    # cornerTan = math.tan(edgeObj.cornerAngle / 2)
    #
    # boxCentrePoint = startPoint.copy()
    # boxLength = effectiveRadius / cornerTan - centreDistance
    # boxWidth = effectiveRadius * 2
    #
    # lengthDirectionVector = edgeObj.cornerVector.copy()
    # lengthDirectionVector.normalize()
    # lengthDirectionVector.scaleBy(boxLength / 2)
    #
    # if lengthDirectionVector.length < 0.01:
    #     return toolBody
    #
    # heightDirectionVector = edgeObj.edgeVector.copy()
    # heightDirectionVector.normalize()
    # heightDirectionVector.scaleBy(edgeHeight / 2)
    #
    # heightDirectionVector.add(lengthDirectionVector)
    #
    # lengthDirectionVector.normalize()
    #
    # boxCentrePoint.translateBy(heightDirectionVector)
    #
    # #   rotate centreLine Vector (cornerVector) by 90deg to get width direction vector
    # orthogonalMatrix = adsk.core.Matrix3D.create()
    # orthogonalMatrix.setToRotation(math.pi / 2, edgeObj.edgeVector, boxCentrePoint)
    #
    # widthDirectionVector = edgeObj.cornerVector.copy()
    # widthDirectionVector.transformBy(orthogonalMatrix)
    #
    # boxLength = 0.001 if (boxLength < 0.001) else boxLength
    #
    # boundaryBox = adsk.core.OrientedBoundingBox3D.create(
    #     centerPoint=boxCentrePoint,
    #     lengthDirection=lengthDirectionVector,
    #     widthDirection=widthDirectionVector,
    #     length=boxLength,
    #     width=boxWidth,
    #     height=edgeHeight,
    # )
    #
    # box = tempBrepMgr.createBox(boundaryBox)
    #
    # tempBrepMgr.booleanOperation(
    #     targetBody=toolBody,
    #     toolBody=box,
    #     booleanType=adsk.fusion.BooleanTypes.UnionBooleanType,
    # )
    #
    # return toolBody


def createDogeBones(inputs: DogeboneFeatureInput):
    logger.info("Creating dogbones")

    tempBrepMgr = adsk.fusion.TemporaryBRepManager.get()
    startTlMarker = _design.timeline.markerPosition

    # [str] faceId
    # face [adsk.fusion.BRepFace]
    for faceId, face in inputs.faces.items():

        toolBodies = None

        # TODO: topFace
        topFace = None

        # if param.fromTop:
        #     topFace, topFaceRefPoint = dbUtils.getTopFace(occurrenceFaces[0].native)
        #     logger.debug(f"topFace ref point: {topFaceRefPoint.asArray()}")
        #     logger.info(f"Processing holes from top face - {topFace.tempId}")
        #     debugFace(topFace)

        edgesForFace = getDogboneEdgesForFace(face)
        if len(edgesForFace) == 0:
            logger.debug(f"No edges found for face {face.entityToken}")
            continue

        for edge in edgesForFace:
            if not toolBodies:
                toolBodies = getToolBody(edge, face, inputs, topFace=topFace)
            else:
                tempBrepMgr.booleanOperation(
                    toolBodies,
                    getToolBody(edge, face, inputs, topFace=topFace),
                    adsk.fusion.BooleanTypes.UnionBooleanType,
                )

        baseFeature = _rootComp.features.baseFeatures.add()
        baseFeature.name = "doge"
        saveToFeature(baseFeature, inputs, face)

        baseFeature.startEdit()
        dbB = _rootComp.bRepBodies.add(toolBodies, baseFeature)
        dbB.name = "dogboneTool"
        baseFeature.finishEdit()

        toolCollection = adsk.core.ObjectCollection.create()
        toolCollection.add(baseFeature.bodies.item(0))

        activeBody = native(face).body

        combineInput = _rootComp.features.combineFeatures.createInput(
            targetBody=activeBody, toolBodies=toolCollection
        )
        combineInput.isKeepToolBodies = False
        combineInput.isNewComponent = False
        combineInput.operation = (
            adsk.fusion.FeatureOperations.CutFeatureOperation
        )
        combine = _rootComp.features.combineFeatures.add(combineInput)
        combine.name = 'doge_combine'

    endTlMarker = _design.timeline.markerPosition - 1
    if endTlMarker - startTlMarker > 0:
        timelineGroup = _design.timeline.timelineGroups.add(
            startTlMarker, endTlMarker
        )
        timelineGroup.name = "dogbone"


def getDogboneEdgesForFace(face) -> List[adsk.fusion.BRepEdge]:
    faceNormal = getFaceNormal(face)

    faceEdgesSet = {edge.entityToken for edge in face.edges}
    faceVertices = [vertex for vertex in face.vertices]

    allEdges = {}

    for vertex in faceVertices:
        allEdges.update({edge.entityToken: edge for edge in vertex.edges})

    # TODO: seems we can skip the filtering, by just saying that the edges of a face, won't be a candidate
    # because it's not parallel to the normal
    candidateEdgesId = set(allEdges.keys()) - faceEdgesSet
    candidateEdges = [allEdges[edgeId] for edgeId in candidateEdgesId]

    edges: List[adsk.fusion.BRepEdge] = []

    for edge in candidateEdges:
        if not edge.isValid or edge.isDegenerate:
            continue

        if edge.geometry.curveType != adsk.core.Curve3DTypes.Line3DCurveType:
            continue

        edgeVector = getEdgeVector(edge, refFace=face)
        edgeVector.normalize()

        if not edgeVector.isParallelTo(faceNormal):
            continue

        if edgeVector.isEqualTo(faceNormal):
            continue

        face1, face2 = edge.faces

        if face1.geometry.objectType != adsk.core.Plane.classType():
            continue

        if face2.geometry.objectType != adsk.core.Plane.classType():
            continue

        angle = getAngleBetweenFaces(edge) * 180 / math.pi
        if abs(angle - 90) > 0.001:
            continue

        edges.append(edge)

    return edges
