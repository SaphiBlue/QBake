import bpy
from pathlib import Path
import os
import json

bpy.ops.preferences.addon_enable(module="QBake")

from QBake.classes import qbake_bake
from QBake.classes import status




def main():

    _status = status.status()

    _status.write({
        'status': 'INIT'
    })

    bpy.context.scene.qbake.export = True
    qbake = qbake_bake.qbake_bake(None, bpy.context)
    qbake.obj = bpy.context.view_layer.objects.active

    qbake.prepare_bake()

    run = True
    while run:        
        
        _status.write({
            'status': 'BAKING',
            'current': qbake.count_current + 1,
            'total': qbake.count_total
        })
        remaining = qbake.bake_sequence()
        if(remaining <= 0):
            run = False

    _status.write({
        'status': 'DONE'
    })

    #_status.delete()

if __name__ == "__main__":
    main()