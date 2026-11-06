import * as THREE from "three";
import { OrbitControls } from "./vendor/three/OrbitControls.js";
import { STLLoader } from "./vendor/three/STLLoader.js";

export async function showStl(host, url, label, signal) {
  signal.throwIfAborted();
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error(`STL: HTTP ${response.status}`);
  const bytes = await response.arrayBuffer();
  signal.throwIfAborted();

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.domElement.setAttribute("role", "img");
  renderer.domElement.setAttribute("aria-label", `3D preview of ${label} spacer`);

  const geometry = new STLLoader().parse(bytes);
  geometry.center();
  geometry.computeBoundingSphere();
  const radius = geometry.boundingSphere.radius;
  const material = new THREE.MeshStandardMaterial({ color: 0x6083c2, roughness: 0.52 });
  const scene = new THREE.Scene();
  scene.add(new THREE.Mesh(geometry, material));
  scene.add(new THREE.HemisphereLight(0xffffff, 0x60718a, 2.3));
  const key = new THREE.DirectionalLight(0xffffff, 2.2);
  key.position.set(-1, -2, 4);
  scene.add(key);

  const camera = new THREE.PerspectiveCamera(34, 1, radius / 100, radius * 40);
  camera.up.set(0, 0, 1);
  camera.position.set(1, -1.35, 1.45).setLength(radius * 3.5);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.minDistance = radius * 1.25;
  controls.maxDistance = radius * 10;
  controls.enablePan = false;
  controls.update();

  const render = () => renderer.render(scene, camera);
  controls.addEventListener("change", render);
  const resize = new ResizeObserver(() => {
    const { clientWidth: width, clientHeight: height } = host;
    if (!width || !height) return;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
    render();
  });
  host.append(renderer.domElement);
  resize.observe(host);

  signal.addEventListener("abort", () => {
    resize.disconnect();
    controls.dispose();
    material.dispose();
    geometry.dispose();
    renderer.dispose();
    renderer.forceContextLoss();
    renderer.domElement.remove();
  }, { once: true });
}
