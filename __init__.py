##
# Blender Addon Qbake (Quantum Bake)
#Copyright (C) 2026 Saphi
##
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.


bl_info = {
    "name": "Quantum Bake",
    "description": "Bakes textures in bulk based on thier node setup",
    "author": "Saphi",
    "version": (1, 0, 16),
    "blender": (5, 2, 0),
    "category": "Node",
    "location": "Shader Editor > Add > Output > Q Baker Container",
    "doc_url": "https://github.com/SaphiBlue/QBake",
    "tracker_url": "https://github.com/SaphiBlue/QBake/issues"
}

import bpy

from . import operators
from . import nodes
from . import ui
from . import qbake_global_props


modules = (
    qbake_global_props,
    operators,
    nodes,
    ui
)

def register():
    for module in modules:
        if hasattr(module, 'register'):
            module.register()

def unregister():
    for module in modules:
        if hasattr(module, 'unregister'):
            module.unregister()    