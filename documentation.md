# Underwater Voxel Engine Documentation

## Overview
This project renders an underwater voxel world using permitted GL/GLU/GLUT functions. It features Perlin-noise seabed, coral reefs, seaweed sway, bubbles, caves with darker lighting, color-only lighting, optional Phong-like shading, and a compact top-right minimap that tracks the player and shows an arrow for facing direction.

## Modules
- `main.py`: Initializes window, sets projection, runs display and input callbacks, draws scene and minimap.
- `camera.py`: Manages position, movement (WASD/QE), yaw/pitch (IJKL), and visibility flag when inside seaweed.
- `map_manager.py`: Generates terrain with Perlin noise, builds coral reefs and seaweed patches, creates caves, handles color lighting and caustics, draws bubbles, seaweed and coral rods, provides spawn position and minimap.
- `config.py`: Central settings, block palette, sizes, lighting params, minimap/window, seaweed tuning, cave darkening, and Phong toggle.
- `permittedFunctions.txt`: Allowed GL/GLU/GLUT calls.

## Key Features
- Seabed generation via Perlin noise, producing dunes and varied heights.
- Coral reefs: at least one reef sized within min/max bounds; additional small coral rods placed on blocks.
- Seaweed: two stacked, slender rectangles that sway horizontally; player passes through; visibility flag set false when inside.
- Bubbles: small spheres spawn randomly at seabed and rise over time.
- Caves: pockets carved under seabed; lighting darkens inside cave shadow.
- Color-only lighting: ambient + depth darkening; moving caustics on seabed.
- Phong-like shading (optional): CPU-side diffuse/spec highlights applied to top blocks using height gradients.
- Minimap: compact viewport that follows the player; color-coded cells; white arrow shows player position and facing.
- Coral reef shapes: generated with a noise-based mask for natural, non-square forms.
- Performance: view-based culling draws only nearby blocks; optional GPU backface culling reduces overdraw.
- Block sizing: seaweeds and small corals use thinner/smaller scaled cubes; seabed, rocks, and large corals use normal-sized blocks.

## Configuration
See `config.py`:
- `MAP_SIZE`, `MAX_HEIGHT`, `MIN_HEIGHT`
- `WINDOW_WIDTH`, `WINDOW_HEIGHT`
- `BLOCK_TYPES`: sand(10), rock(11), corals(12–15), seaweed(16), demo(1–3)
- Lighting: `LIGHT_AMBIENT`, `LIGHT_DEPTH_DARKEN`, caustics `CAUSTICS_*`
- Reef sizing: `CORAL_REEF_MIN_SIZE`, `CORAL_REEF_MAX_SIZE`
- Seaweed tuning: `SEAWEED_SEG_LEN`, `SEAWEED_SWAY_AMP`
- Caves: `CAVE_DARKEN`
- Phong toggle/params: `PHONG_ON`, `PHONG_LIGHT_DIR`, `PHONG_AMB`, `PHONG_DIFF`, `PHONG_SPEC`, `PHONG_SHININESS`
- Minimap: `MINIMAP_CELL`, `MINIMAP_VIEW_SIZE`, `MINIMAP_MARGIN`, `USE_DYNAMIC_MINIMAP`
- Rendering cull: `USE_VIEW_CULLING`, `DRAW_RADIUS`
- GPU option: `GPU_BACKFACE_CULL`
- Multithreading toggle (reserved): `USE_MULTITHREADING`

## Controls
- Movement: W/A/S/D, Ascend: Q, Descend: E
- Look: I/K (pitch), J/L (yaw)

## Rendering and Permitted Calls
Drawing uses only allowed APIs: matrix stack ops, color, transform, quads, cubes/spheres, perspective, lookAt, orthographic for minimap. No fixed-function lighting is enabled; shading is done by CPU via color modulation.

## Spawn Position
MapManager computes a spawn location with clear surroundings on sand and sets camera above ground. Adjust logic via `_has_obstacle_near` if needed.

## Minimap
Rendered in screen space with orthographic projection; positioned at top-right. The minimap shows a cropped region around the player using `MINIMAP_VIEW_SIZE` and smaller `MINIMAP_CELL` pixels. A white triangle indicates player position and facing.

## Extending
- Add additional reef regions by appending to `coral_reefs` and using the noise mask for organic boundaries.
- Tune seaweed sway and heights via config to match desired aesthetics.
- Increase cave density by changing `_generate_caves` threshold and ranges.
- Toggle Phong shading by setting `PHONG_ON = True` in `config.py`.
- Improve performance by increasing `DRAW_RADIUS` judiciously or turning off `USE_VIEW_CULLING`. Backface culling can be toggled via `GPU_BACKFACE_CULL`.

## Running
From the project directory:

```bash
python main.py
```

Ensure your environment has PyOpenGL and GLUT installed. The app uses only permitted functions listed in `permittedFunctions.txt`.
