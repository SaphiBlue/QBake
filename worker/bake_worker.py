import bpy
from pathlib import Path
import os
import json
import sys

bpy.ops.preferences.addon_enable(module="QBake")

from QBake.classes import qbake_bake
from QBake.classes import status







def main():
    _status = status.status()

    _status.write({
        'status': 'INIT'
    })
    
    args = sys.argv


    material_name = None

    obj = bpy.context.view_layer.objects.active
    target_material = None
    node_id = None

    if "--material" in args:
        index = args.index("--material")
        material_name = args[index + 1]

    for material in obj.data.materials:
        if(material.name_full == material_name):
            target_material = material
        

    
    bpy.context.scene.qbake.export = True
    qbake = qbake_bake.qbake_bake(None, bpy.context, node_id=node_id, material=target_material, status = _status)
    qbake.obj = obj

    






    qbake.bake_all()


    _status.write({
        'status': 'DONE'
    })

    #_status.delete()

if __name__ == "__main__":
    main()