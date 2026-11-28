import { assembly } from "tscircuit"

import { Cuboid, Cylinder, ExtrudeLinear, Polygon, Subtract, Translate, Union } from "jscad-fiber/model"

// External installation geometry. Z=0 is the front motor mounting face.
// Rotating the port edge to +Y keeps the plug openings visible in the edge view.
function section(width: number, depth: number, clip: number, z: number, height: number) {
  const x = width / 2, y = depth / 2
  const points: [number, number][] = [
    [-x+clip,-y], [x-clip,-y], [x,-y+clip], [x,y-clip],
    [x-clip,y], [-x+clip,y], [-x,y-clip], [-x,-y+clip],
  ]
  return <Translate offset={[0,0,z]}><ExtrudeLinear height={height}><Polygon points={points}/></ExtrudeLinear></Translate>
}

function bore(x: number, y: number, name: string) {
  const points: [number, number][] = Array.from({length:40}, (_,i) => [
    1.5*Math.cos(i*Math.PI/20), 1.5*Math.sin(i*Math.PI/20),
  ])
  return <Translate offset={[x,y,-4.5]}><ExtrudeLinear height={4.5} topOutlineName={name}><Polygon points={points}/></ExtrudeLinear></Translate>
}

function MountedMotor() {
  return <Union>
    <Subtract>
      {section(42.3,42.3,3,-38,38)}
      {bore(-15.5,-15.5,"H1")}{bore(15.5,-15.5,"H2")}{bore(-15.5,15.5,"H3")}{bore(15.5,15.5,"H4")}
    </Subtract>
    <Cylinder radius={11} height={2} center={[0,0,1]} />
    <Subtract>
      <Cylinder radius={2.5} height={23.5} center={[0,0,11.75]} />
      <Cuboid size={[10,8,20]} center={[0,6,13.5]}/>
    </Subtract>
    <Subtract>
      {section(45.30,45.32,4,-50.30,12.30)}
      {/* External ports are represented by their shell apertures at the CAD coordinates. */}
      <Cuboid size={[9.54,5,4.2]} center={[6,22,-44.63]}/>
      <Cuboid size={[9.54,5,4.2]} center={[-7,22,-44.63]}/>
      <Cuboid size={[4,12,5.5]} center={[-22.5,-4.2,-45.75]}/>
    </Subtract>
  </Union>
}

export default () => (
  <assembly.device>
    <assembly.printedpart name="motor" jscad={<MountedMotor />} />
    <assembly.part name="assembled" modelUrl="./motor-mounting.glb" />
    <assembly.part name="shaftView" cadModel={{glbUrl:"./motor-mounting.glb",rotationOffset:{x:0,y:0,z:180}}} />
    <assembly.drawing.page name="mounting" width={300} height={223}>
      <assembly.drawing.note text="NEMA17  /  Motor with integrated USB controller" paperX={-141} paperY={100} fontSize={5.5} />
      <assembly.drawing.note text="MOUNTING REFERENCE   •   v1.0.58   •   COVER R2 / TRAY R1   •   mm" paperX={-141} paperY={90} fontSize={3.4} />
      <assembly.drawing.partview name="front" displayName="Front mounting face" partRef=".motor" direction="z+" width={54} height={54} centerX={-89} centerY={46}>
        <assembly.drawing.dimension fromRef=".motor > .H1" toRef=".motor > .H2" axis="x" />
        <assembly.drawing.dimension fromRef=".motor > .H1" toRef=".motor > .H3" axis="y" />
        <assembly.drawing.dimension widthOfView />
        <assembly.drawing.dimension heightOfView />
      </assembly.drawing.partview>
      <assembly.drawing.partview name="iso" displayName="Controller end" partRef=".assembled" direction="isometric" width={73} height={66} centerX={98} centerY={47}/>
      <assembly.drawing.partview name="shaftIso" displayName="Shaft end" partRef=".shaftView" direction="isometric" width={73} height={66} centerX={14} centerY={47} />
      <assembly.drawing.partview name="ports" displayName="USB-C edge   /   DATA left, PWR right" partRef=".motor" direction="y-" width={66} height={69} centerX={-88} centerY={-39}>
        <assembly.drawing.dimension heightOfView />
      </assembly.drawing.partview>
      <assembly.drawing.note text="Mounting face" paperX={-5} paperY={-10} fontSize={4} />
      <assembly.drawing.note text="4 × M3 on a 31 × 31 square, centered on shaft" paperX={-5} paperY={-19} fontSize={3.2}/>
      <assembly.drawing.note text="Ø22 pilot × 2 high  /  Ø5 shaft × 23.5 projection" paperX={-5} paperY={-27} fontSize={3.2}/>
      <assembly.drawing.note text="Motor frame 42.3 × 42.3 × 38" paperX={-5} paperY={-35} fontSize={3.2}/>
      <assembly.drawing.note text="Rear controller" paperX={-5} paperY={-48} fontSize={4}/>
      <assembly.drawing.note text="45.30 × 45.32 enclosure  /  12.30 behind motor" paperX={-5} paperY={-57} fontSize={3.2}/>
      <assembly.drawing.note text="USB-C DATA and PWR on one edge, 13 apart" paperX={-5} paperY={-65} fontSize={3.2}/>
      <assembly.drawing.note text="50.3 face to lid  /  73.8 shaft tip to lid" paperX={-5} paperY={-73} fontSize={3.2}/>
      <assembly.drawing.note text="Reference motor: 17HE15-1504S from the packing model. Confirm the fitted motor before machining." paperX={-141} paperY={-94} fontSize={3.5}/>
      <assembly.drawing.note text="Rigid envelope excludes label thickness, flexible motor lead, and inserted USB plugs. Nominal dimensions." paperX={-141} paperY={-102} fontSize={3.2}/>
    </assembly.drawing.page>
  </assembly.device>
)
