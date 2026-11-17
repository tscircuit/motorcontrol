"""OpenCascade CAD tool script. All dimensions mm; draft fit study, not production release."""
import cadquery as cq
import json, math, pathlib, gzip, base64, struct
from svgpathtools import parse_path
import xml.etree.ElementTree as ET

ROOT=pathlib.Path(__file__).resolve().parent
MODELS=ROOT/'models'; REPORTS=ROOT/'reports'
MODELS.mkdir(exist_ok=True); REPORTS.mkdir(exist_ok=True)
PARTS=[]
BASE_HEIGHT=3.4
FLOOR=1.0
COVER_HEIGHT=6.8
ROOF=1.4
PCB_BOTTOM=BASE_HEIGHT
PCB_TOP=PCB_BOTTOM+1.6
CAD_OFFSET=PCB_BOTTOM+.8
COVER_TOP=PCB_TOP+COVER_HEIGHT
CEILING=COVER_TOP-ROOF
SCREW_SEAT=COVER_TOP-3.2
RECESS_DEPTH=.30
HEADS=[]
HEAD_POCKET_DIA=6.6
SHAFT_BORE_DIA=3.6
POST_DIA=8.4
ENTRY_DIA=7.0
def box(w,d,h,x=0,y=0,z=0):
    return cq.Workplane('XY').box(w,d,h,centered=(True,True,False)).translate((x,y,z)).val()
def cylinder(r,h,x=0,y=0,z=0):
    return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))
def rounded(w,d,r,z,h):
    return cq.Workplane('XY').rect(w,d).extrude(h).edges('|Z').fillet(r).translate((0,0,z)).val()
def mesh(shape):
    verts,faces=shape.tessellate(.2,.45)
    return {'positions':[round(v,3) for p in verts for v in p.toTuple()], 'indices':[i for f in faces for i in f]}
def save(name,shape,color,group,export=True):
    # Orient the reference motor's connector toward +X, matching the PCB JST edge.
    if group=='motor':shape=shape.rotate((0,0,0),(0,0,1),90)
    if not shape.isValid(): raise RuntimeError('Invalid CAD: '+name)
    if export:
        cq.exporters.export(shape,str(MODELS/(name+'.step')))
        cq.exporters.export(shape,str(MODELS/(name+'.stl')),tolerance=.06,angularTolerance=.16)
    PARTS.append(dict(name=name,color=color,group=group,**mesh(shape)))
    return shape

# Reference reconstruction of Josh's recommended Hanpose 17HS3401S.
# Rear seats, endcap split and connector are provisional, not manufacturer STEP.
def motor_plate(z,h):
    return cq.Workplane('XY').rect(42,42).extrude(h).edges('|Z').chamfer(2.3).translate((0,0,z)).val()
rear=motor_plate(-7,7)
for x in [-15.5,15.5]:
    for y in [-15.5,15.5]:
        rear=rear.cut(cylinder(1.7,7.2,x,y,-7.1)).cut(cylinder(3,2,x,y,-2))
rear=rear.cut(cylinder(5,1,0,0,-.9))
save('motor-reference-rear',rear,'#aeb5bd','motor')
body=motor_plate(-28,21)
save('motor-reference-body',body,'#262c31','motor')
front=motor_plate(-34,6)
for x in [-15.5,15.5]:
    for y in [-15.5,15.5]:front=front.cut(cylinder(1.5,4.5,x,y,-34.1))
front=front.fuse(cylinder(11,2,0,0,-36))
save('motor-reference-front',front,'#b8bec4','motor')
shaft=cylinder(2.5,20,0,0,-54).cut(box(8,4,15,0,4,-54))
save('motor-reference-shaft',shaft,'#b8bec4','motor')
connector=box(14,4.5,5.5,0,-22,-7)
connector=connector.cut(box(11.8,3,3.7,0,-23,-6.4))
save('motor-reference-connector',connector,'#d9d6cd','motor')
motor=cq.Compound.makeCompound([rear,body,front,shaft,connector]).rotate((0,0,0),(0,0,1),90)
cq.exporters.export(motor,str(MODELS/'hanpose-17HS3401S-reference-reconstruction.step'))

# Black insulating base with 3.4-mm support and a 1.0-mm floor.
# PCB bottom 3.4, top 5.0; highest resolved part is Z=9.8.
base=motor_plate(0,BASE_HEIGHT).cut(cq.Workplane('XY').rect(39.2,39.2).extrude(BASE_HEIGHT-FLOOR+.1).edges('|Z').chamfer(1.6).translate((0,0,FLOOR)).val())
spacer=cq.Workplane('XY').rect(42,42).extrude(FLOOR).edges('|Z').chamfer(2.3).val().cut(cylinder(11.3,FLOOR+.3,0,0,-.1))
for x in [-15.5,15.5]:
    for y in [-15.5,15.5]:
        spacer=spacer.fuse(cylinder(5,BASE_HEIGHT,x,y)).cut(cylinder(SHAFT_BORE_DIA/2,BASE_HEIGHT+.2,x,y,-.1))
base=base.fuse(spacer).cut(cylinder(11.3,BASE_HEIGHT+.2,0,0,-.1))
for x in [-15.5,15.5]:
    for y in [-15.5,15.5]:base=base.cut(cylinder(SHAFT_BORE_DIA/2,BASE_HEIGHT+.2,x,y,-.1))

# Flush cap: same 42 x 42 outline and corner clips as motor, shared 31-mm M3 pattern.
# It sits above the PCB rather than wrapping around the 42.30 x 42.32 PCB edges.
cap=motor_plate(PCB_TOP,COVER_HEIGHT).cut(cq.Workplane('XY').rect(39.6,39.6).extrude(COVER_HEIGHT-ROOF+.1).edges('|Z').chamfer(1.6).translate((0,0,PCB_TOP-.1)).val())
for x in [-15.5,15.5]:
    for y in [-15.5,15.5]:
        cap=cap.fuse(cylinder(POST_DIA/2,COVER_HEIGHT,x,y,PCB_TOP))
        cap=cap.cut(cylinder(SHAFT_BORE_DIA/2,COVER_HEIGHT+.2,x,y,PCB_TOP-.1))
        # Round counterbore for a nominal 5.5-mm diameter x 3-mm M3 cap head.
        cap=cap.cut(cylinder(HEAD_POCKET_DIA/2,3.3,x,y,SCREW_SEAT))
        cap=cap.cut(cq.Solid.makeCone(HEAD_POCKET_DIA/2,ENTRY_DIA/2,.2,cq.Vector(x,y,COVER_TOP-.2)))
# Fit the openings to the actual USB-C shell envelopes, with 0.30-mm
# clearance above and on each side. The sockets project beyond the outer wall.
usb_openings=[]
for entry in json.loads((REPORTS/'component-envelopes.json').read_text()):
    if entry['name'] not in ['J_USB','J_MOTOR_USB']:continue
    lo=entry['min'];hi=entry['max']
    top=hi[2]+CAD_OFFSET+.30;bottom=PCB_TOP-.10;width=hi[0]-lo[0]+.60
    cap=cap.cut(box(width,6,top-bottom,(lo[0]+hi[0])/2,21.5,bottom))
    usb_openings.append({'part':entry['name'],'width_mm':width,'opening_top_z_mm':top,'opening_bottom_z_mm':bottom,'shell_top_z_mm':hi[2]+CAD_OFFSET,'top_clearance_mm':.30,'side_clearance_mm':.30})
(REPORTS/'usb-opening-dimensions.json').write_text(json.dumps(usb_openings,indent=2))
cap=cap.cut(box(6,11.3,5.2,21.5,-4.65,PCB_TOP-.1))
for y in [-10,-5,0,5,10]:cap=cap.cut(box(4,1.2,3.4,-20.5,y,PCB_TOP+1.6))
for x in [-10,-5,0,5,10]:cap=cap.cut(box(1.2,4,3.4,x,-20.5,PCB_TOP+1.6))

# Use the connector's native geometry below the PCB; its complete AABB includes
# empty space between the inboard tails and the overhanging plastic body.
jst_native=cq.importers.importStep(str(ROOT/'source/J1-S4B-PH-K-S.step')).val()
jst_placed=jst_native.translate((0,-3.25,0)).rotate((0,0,0),(0,0,1),90).translate((16.15,-4.65,PCB_TOP))
def component_clearance_tools(entry,case_part,clearance):
    if entry['name']=='J1' and case_part=='base':
        below=jst_placed.intersect(box(100,100,20,z=BASE_HEIGHT+clearance-20))
        result=[]
        for part in below.Solids():
            b=part.BoundingBox()
            result.append(box(b.xlen+2*clearance,b.ylen+2*clearance,b.zlen+2*clearance,(b.xmin+b.xmax)/2,(b.ymin+b.ymax)/2,b.zmin-clearance))
        return result
    lo=entry['min'];hi=entry['max'];d=[hi[i]-lo[i]+2*clearance for i in range(3)]
    if min(d)<=0:return []
    return [box(d[0],d[1],d[2],(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]+CAD_OFFSET-clearance)]

# Board-specific clearance reliefs leave component envelopes + 0.30 mm untouched.
env=json.loads((REPORTS/'component-envelopes.json').read_text())
reliefs=[]
for entry in env:
    for name in ['cap','base']:
        for bounds in component_clearance_tools(entry,name,.30):
            solid=cap if name=='cap' else base
            vol=solid.intersect(bounds).Volume()
            if vol>1e-5:
                reliefs.append({'part':entry['name'],'case_part':name,'relief_mm3':round(vol,6)})
                if name=='cap':cap=cap.cut(bounds)
                else:base=base.cut(bounds)
base=cq.Workplane(obj=base).faces('<Z').edges().chamfer(.3).val()
save('insulating-base-draft',base,'#24282d','base')
(REPORTS/'component-reliefs.json').write_text(json.dumps(reliefs,indent=2))

# Exact official text-only wordmark, sampled at sub-0.02mm spacing for shallow cut.
svg_path=ROOT/'source/tscircuit-wordmark-text.svg'
svg=ET.parse(svg_path).getroot(); vb=list(map(float,svg.attrib['viewBox'].split()))
scale=25/vb[2]; logo_faces=[]
for element in svg.iter():
    if not element.tag.endswith('path'):continue
    path=parse_path(element.attrib['d']); wires=[]
    for sub in path.continuous_subpaths():
        pts=[]
        for seg in sub:
            count=max(2,math.ceil(seg.length()*scale/.15))
            for k in range(count):
                p=seg.point(k/count)
                pts.append(cq.Vector((p.real-vb[0])*scale-12.5,-((p.imag-vb[1])*scale-vb[3]*scale/2),0))
        if len(pts)>2:wires.append(cq.Wire.makePolygon(pts,close=True))
    # Official lettering contours have no enclosed counters in this wordmark.
    for wire in wires:logo_faces.append(cq.Face.makeFromWires(wire))
logo=cq.Compound.makeCompound([cq.Solid.extrudeLinear(f.outerWire(),[],cq.Vector(0,0,.5)) for f in logo_faces])
cut_logo=logo.rotate((0,0,0),(0,0,1),180).translate((0,0,COVER_TOP-RECESS_DEPTH))
recessed=cap.cut(cut_logo)
save('cover-recessed-logo-draft',recessed,'#24282d','recessed')
save('cover-laser-mark-draft',cap,'#24282d','laser')
sticker_cap=cap.cut(rounded(38.7,19.65,.5,COVER_TOP-.3,.6))
save('cover-sticker-pocket-draft',sticker_cap,'#24282d','sticker')
label=box(38.1,19.05,.15,z=COVER_TOP-.29)
save('sticker-envelope',label,'#f5f5f2','label')

# Head-only envelopes, with hex drive, for illustrating the recessed fastening.
for x in [-15.5,15.5]:
    for y in [-15.5,15.5]:
        head=cylinder(2.75,3,x,y,SCREW_SEAT)
        socket=cq.Workplane('XY').polygon(6,2.5/math.cos(math.pi/6)).extrude(1.4).translate((x,y,COVER_TOP-1.5)).val()
        head=head.cut(socket)
        HEADS.append(head)
        save('recessed-M3-head-'+str(x)+'-'+str(y),head,'#79838c','hardware',export=False)

report={
 'status':'DRAFT - black PCB is an appearance assumption; physical fit and motor identity unverified',
 'board':{'version':'1.0.57','size_mm':[42.2999916,42.3200068,1.6],'bottom_z':PCB_BOTTOM,'top_z':PCB_TOP,'component_z_max':CAD_OFFSET+5.6},
 'cap':{'outside_mm':[42,42,COVER_HEIGHT],'bottom_z':PCB_TOP,'top_z':COVER_TOP,'ceiling_z':CEILING,'nominal_roof_mm':ROOF,'wall_mm':1.2,'highest_component_roof_gap_mm':CEILING-(CAD_OFFSET+5.6),'corner_screws':'4 x shared M3 socket cap nominal at 31-mm pitch; under-head length to be measured','corner_clip_mm':2.3,'side_clearance_relief_mm':.3,'screw_pocket_diameter_mm':HEAD_POCKET_DIA,'screw_pocket_depth_mm':3.2,'screw_pocket_entry_diameter_mm':ENTRY_DIA,'head_nominal_mm':[5.5,3],'head_top_below_lid_mm':.2,'post_outer_diameter_mm':POST_DIA,'shaft_bore_diameter_mm':SHAFT_BORE_DIA,'nominal_head_radial_clearance_mm':(HEAD_POCKET_DIA-5.5)/2,'nominal_shaft_radial_clearance_mm':(SHAFT_BORE_DIA-3)/2,'post_wall_at_counterbore_mm':(POST_DIA-HEAD_POCKET_DIA)/2,'usb_shell_top_clearance_mm':.30,'finish':'Matte black'},
 'base':{'support_height_mm':BASE_HEIGHT,'floor_mm':FLOOR,'wall_mm':1.4,'bottom_edge_chamfer_mm':.3,'jst_wall':'Continuous exterior; native connector pins checked inside hollow base','outside_mm':[42,42],'center_opening_mm':22.6,'pcb_mounting_pitch_mm':31,'case_mounting_holes_mm':SHAFT_BORE_DIA,'pcb_mounting_holes_mm':3.4},
 'pcb_overhang_per_edge_mm':[.1499958,.1600034],
 'motor':{'reference':'Hanpose 17HS3401S per Josh getting-started guide','source_type':'Reconstructed external reference; NOT downloaded manufacturer STEP','body_mm':[42,42,34],'shaft_diameter_mm':5,'shaft_extension_mm':20,'rear_bolt_pitch_mm':31,'assembly_rotation_z_degrees':90,'connector_edge':'+X','rear_geometry':'PROVISIONAL: recesses, connector, endcap splits, screw thread engagement'},
 'branding':{'recessed_depth_mm':RECESS_DEPTH,'wordmark_width_mm':25,'stock_label':'OnlineLabels OL1067WX 1.5 x 0.75 inch','qr_removed':True,'readable_link':'motorcontrol.tscircuit.com','sticker_mm':[38.1,19.05,.15],'sticker_corner_radius_mm':0,'pocket_mm':[38.7,19.65,.3],'pocket_corner_radius_mm':.5,'pocket_floor_mm':ROOF-.3,'sticker_top_below_lid_mm':.14,'sticker_application':'Print pocket into the lid, finish smooth, apply printed adhesive label after printing','print_orientation':'Sticker lid exterior face up with removable roof supports; plain laser lid exterior face down. Verify in slicer.','laser_contrast':'Illustrative; requires exact-filament test'},
 'unverified':['Actual kit motor model','Motor rear geometry and original tie screws','Physical PCB revision matches v1.0.57','USB plug overmold size and insertion','JST mating cable and bend radius','Assembly tolerances','Loaded thermal performance','ESD performance; ordinary printed case is not ESD shielding']
}
(REPORTS/'design-parameters.json').write_text(json.dumps(report,indent=2))

# Robust CAD intersection volumes against component AABB envelopes (conservative).
env=json.loads((REPORTS/'component-envelopes.json').read_text())
collisions=[]
for entry in env:
    for name,solid in [('cap',cap),('base',base)]:
        for bounds in component_clearance_tools(entry,name,0):
            vol=solid.intersect(bounds).Volume()
            if vol>1e-5:collisions.append({'part':entry['name'],'case_part':name,'aabb_overlap_mm3':round(vol,6)})
assert base.intersect(jst_placed).Volume()<1e-6,'JST native model must clear the base'
(REPORTS/'component-aabb-collisions.json').write_text(json.dumps(collisions,indent=2))
(ROOT/'source/cad-preview.json.gz').write_bytes(gzip.compress(json.dumps(PARTS,separators=(',',':')).encode()))
for name,solid in [('cap',cap),('base',base)]:
    bb=solid.BoundingBox()
    assert abs(bb.xlen-42)<1e-5 and abs(bb.ylen-42)<1e-5,(name,bb.xlen,bb.ylen)
    assert len(solid.Solids())==1,(name,'disconnected solids',len(solid.Solids()))
assert not collisions,collisions
assert base.intersect(cylinder(11.25,BASE_HEIGHT+.2,0,0,-.1)).Volume()<1e-6,'Center relief must pass through the floor'
for x in [-15.5,15.5]:
    for y in [-15.5,15.5]:assert base.intersect(cylinder(1.65,BASE_HEIGHT+.2,x,y,-.1)).Volume()<1e-6,'Mounting holes must be through holes'
print(json.dumps({'parts':len(PARTS),'collisions':collisions,'reliefs':reliefs,'all_shapes_valid':True,'cap_and_base_footprint_mm':[42,42],'connected_solids_per_part':1}))
