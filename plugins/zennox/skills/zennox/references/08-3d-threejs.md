# 08 — Image → Procedural Three.js Model

Rebuild the object in a reference image as **code** (a function returning a `THREE.Group`),
not as a downloaded mesh. Output is diffable, tiny, animatable and themeable. Approach adapted
from the img2threejs staged-sculpting idea, implemented here as a lean checklist.

## Contents
1. Suitability gate
2. Spec (before any code)
3. Pass-by-pass build
4. Review loop (vision comparison)
5. Factory contract
6. Materials, lighting, performance
7. Embedding in cross-platform apps

---

## 1. Suitability gate

Good fits: hard-surface objects and stylised props (furniture, gadgets, chests, lamps,
vehicles, low-poly characters, logos-as-objects the user owns). Poor fits: photoreal faces,
fur, foliage, cloth with complex folds, scenes with many objects. If poor, say so and offer a
stylised/low-poly version or suggest photogrammetry / an image-to-mesh service instead.

A single image can't show hidden sides: state that unseen faces are inferred (usually by
mirroring/symmetry) and that output is approximate.

## 2. Spec (write it, don't code yet)

Write `object-spec.json` (or a short markdown block) with:
- **Identity features**: the 3–7 things that make it recognisable (e.g. "brass corner caps",
  "arched lid", "keyhole plate"). Fidelity is judged on these.
- **Proportions**: overall bounding box ratios (W:H:D) measured from the image; unit scale
  (1 unit = 1 metre unless told otherwise).
- **Part hierarchy**: root → major masses → sub-parts → details, with primitive per part.
- **Primitive mapping**: Box, RoundedBox (via `ExtrudeGeometry` of a rounded rect), Sphere,
  Cylinder, Cone, Torus, Capsule-equivalent (Cylinder + 2 Spheres if the Three.js version
  lacks Capsule), Lathe (profiles of revolution), Extrude (custom 2D shapes), Tube (curves).
- **Materials per region**: colour (sampled), roughness, metalness, any emissive.
- **Pivot points** for parts that will animate (lid hinge, wheel axle).

Reject your own spec if identity features or proportions are missing — fixing them later costs
more tokens than getting them now.

## 3. Pass-by-pass build

Generate code only for the current pass:
1. **Blockout** — major masses with correct proportions and silhouette. Neutral material.
2. **Primary forms** — main sub-parts, bevels via rounded shapes, correct pivots.
3. **Secondary details** — trims, handles, panels, insets.
4. **Materials** — colours and PBR values per region.
5. **Micro details** — bolts, seams, decals (only if they carry identity).
6. **Animation rig** — named pivot groups and an optional `animate(t)` helper.

## 4. Review loop

After each pass: render from the reference's camera angle (match FOV and elevation roughly),
screenshot, place side-by-side with the reference, and score 1–10 on silhouette, proportion,
identity features, and colour. Below 7 on any → fix that dimension before the next pass.

In Claude.ai: render in an HTML artifact/preview and compare visually. In Claude Code: use
Playwright to screenshot a local page (`10-testing-playwright.md`) and view both images.

## 5. Factory contract

```ts
import * as THREE from "three";

export interface ChestOptions { scale?: number; lidOpen?: number; palette?: Partial<Palette> }

export function createChest(opts: ChestOptions = {}): THREE.Group {
  const root = new THREE.Group(); root.name = "Chest";
  // body, lidPivot (THREE.Group at hinge), lid inside lidPivot, trims…
  // reuse geometries and materials; never allocate inside animation loops
  root.userData.parts = { lidPivot };            // expose animatable parts
  return root;
}

export function disposeGroup(g: THREE.Object3D) {
  g.traverse(o => { if ((o as THREE.Mesh).isMesh) {
    const m = o as THREE.Mesh; m.geometry.dispose();
    (Array.isArray(m.material) ? m.material : [m.material]).forEach(x => x.dispose());
  }});
}
```

Pure function of options, no global state, no network loads. Export to GLB with
`GLTFExporter` if the user needs a file; check the result in a viewer.

## 6. Materials, lighting, performance

- `MeshStandardMaterial` / `MeshPhysicalMaterial`; share materials across parts with the same look.
- Lighting: one key directional light with soft shadow + hemisphere/ambient fill; an
  environment map (`RoomEnvironment` via `PMREMGenerator`) makes metals read correctly.
- Keep segment counts modest (cylinders 16–32 radial); merge static geometry
  (`BufferGeometryUtils.mergeGeometries`) for draw-call reduction; `InstancedMesh` for repeats.
- `renderer.setPixelRatio(Math.min(devicePixelRatio, 2))`; pause rendering when off-screen or
  tab hidden; dispose on unmount.
- Respect reduced motion: no auto-rotation by default when the user prefers reduced motion.

## 7. Embedding in cross-platform apps

- Web/desktop (Tauri/Electron/Capacitor): plain Three.js or React Three Fiber.
- React Native: `expo-gl` + `expo-three` or React Three Fiber's native renderer; test on
  low-end Android.
- Flutter / native: export GLB and use the platform's 3D viewer (SceneKit/RealityKit,
  SceneView/Filament) if a JS runtime isn't available.
- Always provide a static image fallback (poster) for no-WebGL and for performance mode.
