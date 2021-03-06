import bpy
from bpy.app.handlers import persistent
from bpy.props import *
from . mn_execution import nodeTreeChanged
from bpy.types import NodeTree, Node, NodeSocket
from . mn_utils import *


# Node Tree
##################################

class mn_AnimationNodeTree(bpy.types.NodeTree):
    bl_idname = "mn_AnimationNodeTree"
    bl_label = "Animation";
    bl_icon = "ACTION"
    
    isAnimationNodeTree = bpy.props.BoolProperty(default = True)
    
    def update(self):
        nodeTreeChanged()
    


# Node
##################################    
        
        
class AnimationNode:
    @classmethod
    def poll(cls, nodeTree):
        return nodeTree.bl_idname == "mn_AnimationNodeTree"
        
    def callFunctionFromUI(self, layout, functionName, text = "", icon = "NONE", description = ""):
        idName = getNodeFunctionCallOperatorName(description)
        props = layout.operator(idName, text = text, icon = icon)
        props.nodeTreeName = self.id_data.name
        props.nodeName = self.name
        props.functionName = functionName
        
nodeFunctionCallOperators = {}
missingNodeOperators = []

def getNodeFunctionCallOperatorName(description):
    if description in nodeFunctionCallOperators:
        return nodeFunctionCallOperators[description]
    missingNodeOperators.append(description)
    return "mn.call_node_function_fallback"

class CallNodeFunctionFallback(bpy.types.Operator):
    bl_idname = "mn.call_node_function_fallback"
    bl_label = "Call Node Function"
    
    nodeTreeName = StringProperty()
    nodeName = StringProperty()
    functionName = StringProperty()
    
    def invoke(self, context, event):
        invokeNodeFunctionCall(self, context, event)
 
def invokeNodeFunctionCall(self, context, event):
    node = getNode(self.nodeTreeName, self.nodeName)
    getattr(node, self.functionName)()
    return {"FINISHED"}

    
@persistent    
def createMissingOperators(scene):
    for description in missingNodeOperators:
        createNodeFunctionCallOperator(description)
    missingNodeOperators.clear()
    
def createNodeFunctionCallOperator(description):
    if description not in nodeFunctionCallOperators:
    
        id = str(len(nodeFunctionCallOperators))
        idName = "mn.call_node_function_" + id
        nodeFunctionCallOperators[description] = idName
        
        operatorType = type("CallNodeFunction_" + id, (bpy.types.Operator,), {
            "bl_idname" : idName,
            "bl_label" : "Call Node Function",
            "bl_description" : description,
            "invoke" : invokeNodeFunctionCall })
        operatorType.nodeTreeName = StringProperty()
        operatorType.nodeName = StringProperty()
        operatorType.functionName = StringProperty()
        
        bpy.utils.register_class(operatorType)
    

    
    
        
# Node Socket
##################################        
        
class mn_BaseSocket(NodeSocket):
    bl_idname = "mn_BaseSocket"
    bl_label = "Base Socket"
    
    def draw(self, context, layout, node, text):
        displayText = self.getDisplayedName()
        
        row = layout.row(align = True)
        if self.editableCustomName:
            row.prop(self, "customName", text = "")
        else:
            if not self.is_output and not isSocketLinked(self):
                self.drawInput(row, node, displayText)
            else:
                if self.is_output: row.alignment = "RIGHT"
                row.label(displayText)
                
        if self.moveable:
            row.separator()
            moveSockets = [
                row.operator("mn.move_socket", text = "", icon = "TRIA_UP"),
                row.operator("mn.move_socket", text = "", icon = "TRIA_DOWN")]
            for i, socket in enumerate(moveSockets):
                socket.nodeTreeName = node.id_data.name
                socket.nodeName = node.name
                socket.isOutputSocket = self.is_output
                socket.socketIdentifier = self.identifier
                socket.moveUp = i == 0
                
        if self.removeable:
            row.separator()
            removeSocket = row.operator("mn.remove_socket", text = "", icon = "X")
            removeSocket.nodeTreeName = node.id_data.name
            removeSocket.nodeName = node.name
            removeSocket.isOutputSocket = self.is_output
            removeSocket.socketIdentifier = self.identifier
            
    def draw_color(self, context, node):
        return self.drawColor
        
    def copySettingsFrom(self, node):
        self.setStoreableValue(node.getStoreableValue())
        attributes = [prop.identifier for prop in self.bl_rna.properties if not prop.is_readonly]
        for attribute in attributes:
            get = getattr(node, attribute, None)
            setattr(self, attribute, get)
            
    def getDisplayedName(self):
        if self.displayCustomName or self.editableCustomName: return self.customName
        return self.name
        
        
def customNameChanged(self, context):
    if not self.customNameIsUpdating:
        self.customNameIsUpdating = True
        if self.customNameIsVariable:
            self.customName = makeVariableName(self.customName)
        if self.uniqueCustomName:
            customName = self.customName
            self.customName = "temporary name to avoid some errors"
            self.customName = getNotUsedCustomName(self.node, prefix = customName)
        if self.callNodeWhenCustomNameChanged:
            self.node.customSocketNameChanged(self)
        self.customNameIsUpdating = False
        nodeTreeChanged()
        
def makeVariableName(name):
    newName = ""
    for i, char in enumerate(name):
        if len(newName) == 0 and (char.isalpha() or char == "_"):
            newName += char
        elif len(newName) > 0 and (char.isalpha() or char.isnumeric() or char == "_"):
            newName += char
    return newName
    
def getNotUsedCustomName(node, prefix):
    customName = prefix
    while isCustomNameUsed(node, customName):
        customName = prefix + getRandomString(3)
    return customName
    
def isCustomNameUsed(node, name):
    for socket in node.inputs:
        if socket.customName == name: return True
    for socket in node.outputs:
        if socket.customName == name: return True
    return False
    
    
def getSocketVisibility(socket):
    return not socket.hide
def setSocketVisibility(socket, value):
    socket.hide = not value
    
bpy.types.NodeSocket.show = BoolProperty(default = True, get = getSocketVisibility, set = setSocketVisibility)    
    
class mn_SocketProperties:
    editableCustomName = BoolProperty(default = False)
    customName = StringProperty(default = "custom name", update = customNameChanged)
    displayCustomName = BoolProperty(default = False)
    uniqueCustomName = BoolProperty(default = True)
    customNameIsVariable = BoolProperty(default = False)
    customNameIsUpdating = BoolProperty(default = False)
    removeable = BoolProperty(default = False)
    callNodeToRemove = BoolProperty(default = False)
    callNodeWhenCustomNameChanged = BoolProperty(default = False)
    loopAsList = BoolProperty(default = False)
    moveable = BoolProperty(default = False)
    moveGroup = IntProperty(default = 0)
       
        
class RemoveSocketOperator(bpy.types.Operator):
    bl_idname = "mn.remove_socket"
    bl_label = "Remove Socket"
    
    nodeTreeName = StringProperty()
    nodeName = StringProperty()
    isOutputSocket = BoolProperty()
    socketIdentifier = StringProperty()
    
    def execute(self, context):
        node = getNode(self.nodeTreeName, self.nodeName)
        socket = getSocketByIdentifier(node, self.isOutputSocket, self.socketIdentifier)
        if socket.callNodeToRemove:
            node.removeSocket(socket)
        else:
            if self.isOutputSocket: node.outputs.remove(socket)
            else: node.inputs.remove(socket)
        return {'FINISHED'}

class MoveSocketOperator(bpy.types.Operator):
    bl_idname = "mn.move_socket"
    bl_label = "Move Socket"
    
    nodeTreeName = StringProperty()
    nodeName = StringProperty()
    isOutputSocket = BoolProperty()
    socketIdentifier = StringProperty()
    moveUp = BoolProperty()
    
    def execute(self, context):
        node = getNode(self.nodeTreeName, self.nodeName)
        moveSocket = getSocketByIdentifier(node, self.isOutputSocket, self.socketIdentifier)
        sockets = node.outputs if self.isOutputSocket else node.inputs
        moveableSocketIndices = [index for index, socket in enumerate(sockets) if socket.moveable and socket.moveGroup == moveSocket.moveGroup]
        currentIndex = list(sockets).index(moveSocket)
        
        targetIndex = -1
        for index in moveableSocketIndices:
            if self.moveUp and index < currentIndex:
                targetIndex = index
            if not self.moveUp and index > currentIndex:
                targetIndex = index
                break
                
        if targetIndex != -1:
            sockets.move(currentIndex, targetIndex)
            if self.moveUp: sockets.move(targetIndex + 1, currentIndex)
            else: sockets.move(targetIndex - 1, currentIndex)
        return {'FINISHED'}

        

# Register
################################## 

def register_handlers():    
    bpy.app.handlers.scene_update_post.append(createMissingOperators)
    
def unregister_handlers():
    bpy.app.handlers.scene_update_post.remove(createMissingOperators)      