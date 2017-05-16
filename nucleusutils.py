__author__ = 'rainawu'

import pymel.core as pm
import os
from xml.dom import minidom

def getCacheFrameRange(cacheFilePath):
    """
    Parse cache frame range from nCache .xml file.
    :param cacheFilePath: `string` nCache .xml file path
    :return: `list` frame range
    """
    cacheFile = minidom.parse(cacheFilePath)
    range = cacheFile.getElementsByTagName("time")[0].attributes["Range"].value
    timePerFrame = cacheFile.getElementsByTagName("cacheTimePerFrame")[0]\
                            .attributes["TimePerFrame"].value
    start = int(range.split("-")[0]) / int(timePerFrame)
    end = int(range.split("-")[1]) / int(timePerFrame)
    return [start, end]


def getChannelNames(cacheFilePath):
    """
    Parse channel names from nCache .xml file.
    :param cacheFilePath: `string` nCache .xml file path
    :return: `list` channel names
    """
    cacheFile = minidom.parse(cacheFilePath)
    channel0 = cacheFile.getElementsByTagName("channel0")[0].attributes["ChannelName"].value
    channel1 = cacheFile.getElementsByTagName("channel1")[0].attributes["ChannelName"].value
    channel2 = cacheFile.getElementsByTagName("channel2")[0].attributes["ChannelName"].value
    return [channel0, channel1, channel2]


# import hairsystem cache
def importNHairCache(hairSystemNode=None, filePath=None):
    """
    Attach nHair cache.
    :param hairSystemNode: `PyNode` hair system node to attach the cache to
    :param filePath: `string` nCache .xml file path
    :return:
    """
    selection = pm.ls(sl=True, type=["transform", "hairSystem"])
    if not hairSystemNode:
        if selection:
            if selection[0].nodeType() == "hairSystem":
                hairSystemNode = selection[0]
            else:
                shapeNode = selection[0].getShape()
                if shapeNode and shapeNode.nodeType() == "hairSystem":
                    hairSystemNode = shapeNode
        if not hairSystemNode:
            print "Please select/input a hairSystem node to import cache files."
            return False

    if not filePath:
        filePath = pm.fileDialog2(fileFilter="*.xml", dialogStyle=2, fileMode=1)
        if not filePath:
            return False
        else:
            filePath = filePath[0]
    baseDirectory = os.path.split(filePath)[0]
    cacheName = os.path.splitext(os.path.basename(filePath))[0]
    # check if is already connected to a cache
    if hairSystemNode.playFromCache.isConnected():
        replaceCache = pm.confirmDialog(title="Replace Cache",
                         message="{0} is already connected to a cache, "
                                 "do you want to replace the current one?"
                                 .format(hairSystemNode.name()),
                         button=["Yes", "No"],
                         defaultButton="Yes",
                         cancelButton="No",
                         dismissString="No")
        if replaceCache == "No":
            return False
        else:
            oldCache = hairSystemNode.playFromCache.connections(type="cacheFile")[0]
            pm.delete(oldCache)
    channelNames = getChannelNames(filePath)
    print channelNames
    cacheNodeName = pm.cacheFile(af=True, f=cacheName, dir=baseDirectory,
                 cnm=channelNames,
                 ia=["{0}.hairCounts".format(hairSystemNode),
                     "{0}.vertexCounts".format(hairSystemNode),
                     "{0}.positions".format(hairSystemNode)])
    pm.PyNode(cacheNodeName).inRange.connect(hairSystemNode.playFromCache, f=True)
    pm.select(cacheNodeName)
    return True


def hasCache(target):
    """
    Return True if the target node is connected to any cache.
    :param target: `PyNode` hair system node
    :return:
    """
    cacheFiles = target.listHistory(type="cacheFile")
    return True if len(cacheFiles)>0 else False


def setEnableCache(hairSystemNode, flag):
    """
    Enable/Disable the cache connected to the hair system.
    :param hairSystemNode: `PyNode` target hair system node
    :param flag: `bool` True to enable cache, False to disable cache
    :return:
    """
    pm.language.mel.eval("setCacheEnable {0} 0 {{\"{1}\"}};".format(flag, hairSystemNode.name()))


def getSolver(targets=None):
    """
    Get nucleus solver of the targets.
    :param targets: `list` or `PyNode` target hair/cloth nodes
    :return: `list` nucleus solvers
    """
    if not targets:
        targets = pm.ls(sl=True)
    elif not isinstance(targets, "list"):
        targets = [targets]
    result = []
    for target in targets:
        result = result + target.listHistory(type="nucleus", ac=1) + target.listHistory(type="nucleus", ac=1, f=1)
    return list(set(result))
    # return list(set(target.listHistory(type="nucleus", ac=1)+target.listHistory(type="nucleus", ac=1, f=1)))


def getHairSystems(targets=None):
    """
    Get hair systems connected to the targets.
    :param targets: `list` of `PyNode` target nodes
    :return: `list` hair system nodes
    """
    if not targets:
        targets = pm.ls(sl=True)
    elif not isinstance(targets, "list"):
        targets = [targets]
    result = []
    for target in targets:
        if target.nodeType() == "hairSystem":
            result.append(target)
        else:
            result = result + target.listHistory(type="hairSystem", ac=1) + target.listHistory(type="hairSystem", ac=1, f=1)
    return list(set(result))


def getCurves(targets=None):
    """
    Get hair systems curves connected to the targets.
    :param targets: `list` of `PyNode` target nodes
    :return: `list` curve nodes
    """
    if not targets:
        targets = pm.ls(sl=True)
    elif not isinstance(targets, "list"):
        targets = [targets]
    result = []
    for target in targets:
        result = result + target.listHistory(type="nurbsCurve") + target.listHistory(type="nurbsCurve", f=1)
    return list(set(result))


def getFollicles(targets=None):
    """
    Get follicles connected to the targets.
    :param targets: `list` of `PyNode` target nodes
    :return: `list` follicle nodes
    """
    if not targets:
        targets = pm.ls(sl=True)
    elif not isinstance(targets, "list"):
        targets = [targets]
    result = []
    for target in targets:
        result = result + target.listHistory(type="follicle") + target.listHistory(type="follicle", f=1)
    return list(set(result))
    # return getRelativeNode(target, "follicle", 2)
