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

import bpy

from ..classes import qbake_bake

class qbake_operator(bpy.types.Operator):
    """Bake All nodes"""
    bl_idname = "render.qbake_operator"
    bl_label = "Bake all Nodes"

    _timer = None
    qbake = None
    state = ''

    @classmethod
    def poll(cls, context):
        return True

    def modal(self, context, event):
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        if self.state == 'INIT':
            self.qbake = qbake_bake.qbake_bake(operator=self, context=context)
            self.state = 'BAKE'
            
            

        if self.state == 'BAKE':
            self.state = 'WAIT'
            res = self.qbake.bake_sequence()
            
            if res <= 0:
                self.state = 'DONE'
                return {'PASS_THROUGH'}
            self.state = 'BAKE'

        if self.state == 'DONE':
            
            self.done(context)
            return {'FINISHED'}

        return {'PASS_THROUGH'}
        

    def execute(self, context):
        qbake =  qbake_bake.qbake_bake(operator=self, context=context)
        qbake.bake_all()
        return {'FINISHED'}
    
        #self.state = 'INIT'
        #wm = context.window_manager
        #self._timer = wm.event_timer_add(1, window=context.window)
        #wm.modal_handler_add(self)
        #return {'RUNNING_MODAL'}
    
    def done(self, context):
        wm = context.window_manager
        wm.event_timer_remove(self._timer)
        self.state = ''
        self.qbake = None

def register():
    bpy.utils.register_class(qbake_operator)


def unregister():
    bpy.utils.unregister_class(qbake_operator)