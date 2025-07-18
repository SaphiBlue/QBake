bl_info = {
    "name": "Quantum Bake",
    "description": "Bakes Textures in bulk",
    "author": "Saphi",
    "version": (1, 0, 11),
    "blender": (4, 5, 0),
    "category": "Node",
    "location": "Shader Editor > Add > Output > Q Baker Container",
    "doc_url": "https://github.com/SaphiBlue/QBake"
}

import bpy

from . import QBakeGlobalProps
from . import QBakeOperators
from . import QBakeNodes
from . import QBakePanel


modules = (
    QBakeGlobalProps,
    QBakeOperators,
    QBakeNodes,
    QBakePanel,
)

def register():
    for module in modules:
        if hasattr(module, 'register'):
            module.register()

def unregister():
    for module in modules:
        if hasattr(module, 'unregister'):
            module.unregister()    

if __name__ == "__main__":
    register()