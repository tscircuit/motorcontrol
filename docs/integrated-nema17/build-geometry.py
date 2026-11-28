"""Exterior mounting model, in mm. Z=0 is the motor's rear mounting plane."""
from pathlib import Path
import sys
import cadquery as cq
import trimesh
out, cover, tray = map(Path, sys.argv[1:4])
scene = trimesh.Scene()
def solid_mesh(name, shape):
    points, faces = shape.tessellate(.03, .12)
    add(name,trimesh.Trimesh([p.toTuple() for p in points], faces))
def add(name, mesh):
    # Present the shaft toward +Z and the port edge toward +Y.
    mesh.apply_transform(trimesh.transformations.rotation_matrix(3.141592653589793,[0,1,0]))
    scene.add_geometry(mesh,geom_name=name,node_name=name)
def plate(z, h):
    return cq.Workplane('XY').rect(42.3,42.3).extrude(h).edges('|Z').chamfer(3).translate((0,0,z))
def cylinder(radius,z,h):
    return cq.Workplane('XY').circle(radius).extrude(h).translate((0,0,z))
motor=plate(-38,38)
for x in [-15.5,15.5]:
    for y in [-15.5,15.5]:
        motor=motor.cut(cylinder(1.5,-38.1,4.6).translate((x,y,0)))
motor=motor.union(cylinder(11,-40,2))
shaft=cylinder(2.5,-61.5,23.5).cut(cq.Workplane('XY').box(12,8,20).translate((0,6,-51.5)))
solid_mesh('Motor with mounting pilot and shaft',motor.union(shaft).val())
for name,path in [('Flat-top cover R2',cover),('Spacer tray R1',tray)]:
    add(name,trimesh.load_mesh(path))
# glTF uses Y up. Face the rear sockets into the native isometric camera.
scene.apply_transform([[ -1,0,0,0],[0,0,1,0],[0,1,0,0],[0,0,0,1]])
scene.export(out)
print(scene.bounds)
