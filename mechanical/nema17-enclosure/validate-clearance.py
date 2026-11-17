import cadquery as cq,json,math
from pathlib import Path
r=Path(__file__).resolve().parent;models=r/'models'
base=cq.importers.importStep(str(models/'insulating-base-draft.step')).val()
caps={n:cq.importers.importStep(str(models/(f'cover-{f}-draft.step'))).val() for n,f in [('sticker','sticker-pocket'),('laser','laser-mark'),('recessed','recessed-logo')]}
axis_checks=[]
for name,solid in [('base',base),*caps.items()]:
 assert solid.isValid() and len(solid.Solids())==1,name
 bb=solid.BoundingBox();assert abs(bb.xlen-42)<1e-5 and abs(bb.ylen-42)<1e-5
 for x in [-15.5,15.5]:
  for y in [-15.5,15.5]:
   bottom,height=(0,3.4) if name=='base' else (5,6.8)
   bore=cq.Solid.makeCylinder(1.799,height+.2,cq.Vector(x,y,bottom-.1))
   assert solid.intersect(bore).Volume()<1e-6,(name,x,y,'shaft bore')
   if name!='base':
    pocket=cq.Solid.makeCylinder(3.299,3.0,cq.Vector(x,y,8.6))
    assert solid.intersect(pocket).Volume()<1e-6,(name,x,y,'head pocket')
    # At every azimuth the counterbore's outer wall retains material.
    for angle in [i*math.pi/4 for i in range(8)]:
     probe=cq.Solid.makeCylinder(.03,.1,cq.Vector(x+3.7*math.cos(angle),y+3.7*math.sin(angle),9.0))
     assert abs(solid.intersect(probe).Volume()-probe.Volume())<1e-6,(name,x,y,'post wall')
   axis_checks.append({'case':name,'x':x,'y':y,'shaft_bore_clear':True,'head_pocket_clear':name!='base'})
label=cq.importers.importStep(str(models/'sticker-envelope.step')).val();assert label.intersect(caps['sticker']).Volume()<1e-6
# Re-run conservative component checks emitted by the generator.
assert not json.loads((r/'reports/component-aabb-collisions.json').read_text())
report={'revision':'v4','head_pocket_before_mm':6.0,'head_pocket_mm':6.6,'head_diameter_mm':5.5,'head_radial_clearance_before_mm':.25,'head_radial_clearance_mm':.55,'shaft_bore_before_mm':3.4,'shaft_bore_mm':3.6,'shaft_radial_clearance_mm':.3,'entry_diameter_mm':7.0,'counterbore_depth_mm':3.2,'head_seat_z_mm':8.6,'post_outer_diameter_mm':8.4,'nominal_post_wall_at_pocket_mm':.9,'footprint_mm':[42,42],'case_shapes_valid_single_solids':True,'component_collisions':[],'axis_checks':axis_checks,'physical_print_test':'Not performed; printer compensation, shrinkage and motor fit remain unverified'}
(r/'reports/bolt-clearance-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
