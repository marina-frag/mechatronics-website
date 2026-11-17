# FreeCAD → `spot.glb`

Μετατρέπει τη συναρμολόγηση του FreeCAD σε ένα ελαφρύ `.glb` για το site.
Δεν χρειάζεται να ανοίξεις Blender ή FreeCAD: τρέχουν μόνα τους, χωρίς παράθυρο.

```bash
cd ~/mechatronics_web/pipeline
./build_glb.sh
```

Χρόνος εκτέλεσης: ~30 δευτερόλεπτα. Έξοδος στο `out/`:

| Αρχείο | Τι είναι |
|---|---|
| `spot.glb` | Το μοντέλο για το site (Draco, ~1 MB) |
| `spot.blend` | Το ίδιο μοντέλο για έλεγχο στο Blender (μην το διορθώνεις με το χέρι, ξαναγράφεται) |
| `spot_report.json` | Λίστα εξαρτημάτων: όνομα, υποσύστημα, πόδι, τρίγωνα πριν/μετά |

Αν δίπλα υπάρχει το site, το `spot.glb` αντιγράφεται αυτόματα στο `../public/models/` και βγαίνει
και εικόνα για την κάρτα του project στο `../public/projects/spot/render.png`. Από τη ρίζα του site: `npm run glb`.

## Πώς δουλεύει

1. **`freecad_export.py`** (με `freecad.cmd`): ανοίγει το `SPOT_assembly_auto.FCStd` (την αυτόματη συναρμολόγηση, βλ. `tools/assembly/`) και παίρνει
   κάθε άμεσο παιδί του Assembly ως ένα εξάρτημα, μαζί με τη θέση του στη συναρμολόγηση.
   Διαβάζει STL (Mesh), STEP/Part, Body, App::Part και App::Link. Τα ίδια κομμάτια
   γράφονται μία φορά. Γράφει `build/manifest.json` και `build/geometry.bin`.
2. **`blender_build_glb.py`** (με `blender -b`): ενώνει κορυφές, μειώνει τρίγωνα ώστε όλο το
   ρομπότ να χωράει στο `triangle_budget`, βάζει υλικά ανά υποσύστημα, mm → m, origin στο
   κέντρο κάθε κομματιού, και εξάγει `.glb`.

**Το όνομα κάθε εξαρτήματος στο site = το Label του στο FreeCAD.** Δώσε λοιπόν καθαρά ονόματα
στο FreeCAD πριν την εξαγωγή, π.χ. `st3020_servo_LegBL_top` αντί για `SCS15_20220928_ASM001`.

## Όταν αλλάζει η συναρμολόγηση

Αποθήκευσε στο FreeCAD και ξανάτρεξε `./build_glb.sh`. Τίποτα άλλο.

- Κρυμμένα αντικείμενα (Visibility off) **δεν** εξάγονται. Έτσι κρύβεις κάτι από το site.
- Οι θέσεις παίρνονται όπως αποθηκεύτηκαν στο αρχείο, χωρίς recompute.

Άλλο αρχείο ή επιλογές:

```bash
./build_glb.sh "/path/άλλο.FCStd"
./build_glb.sh "" --budget 250000     # λιγότερα τρίγωνα
./build_glb.sh "" --no-draco          # χωρίς συμπίεση
SPOT_OUT=../public/models/spot.glb ./build_glb.sh   # άλλος φάκελος εξόδου
```

## Ρυθμίσεις: `spot_parts.json`

Οι κανόνες `match` είναι regex πάνω στο Label (χωρίς διάκριση πεζών/κεφαλαίων).
Ο πρώτος κανόνας που ταιριάζει κερδίζει.

- `component_rules`: σε ποιο υποσύστημα ανήκει κάθε εξάρτημα (`frame` = Σκελετός,
  `motors` = Κινητήρες, `electronics` = Ηλεκτρονικά). Όσα δεν ταιριάζουν πάνε στο `default_subsystem`.
- `part_material_rules`: υλικά για κομμάτια **μέσα** σε εξαρτήματα από STEP (π.χ. βίδες,
  PCB και connectors του servo).
- `exclude_parts`: αν θέλουμε να πετάξουμε εσωτερικά κομμάτια που δεν φαίνονται (π.χ. `"gear|pcb"`).
- `replace_parts`: εξαρτήματα που στο `.glb` γίνονται απλό σχήμα με τις ίδιες εξωτερικές διαστάσεις.
  Χρησιμοποιείται για CAD κατασκευαστών που οι όροι τους δεν επιτρέπουν αναδιανομή. Σήμερα αφορά τα
  ρουλεμάν NSK 626ZZ από το CADENAS/3Dfindit, που γίνονται δακτύλιος 6 × 19 × 6 mm. Το αρχείο FreeCAD
  της ομάδας κρατά το αρχικό CAD.
- `materials`: χρώματα (hex), metallic, roughness. Τα χρώματα του FreeCAD δεν μεταφέρονται.
- `decimation.triangle_budget`: πόσα τρίγωνα συνολικά (προεπιλογή 400k, καλό για laptop και κινητό).
  Τα τρίγωνα μοιράζονται με ίδια πυκνότητα ανά επιφάνεια, ώστε τα μεγάλα κομμάτια να κρατούν
  λεπτομέρεια. Με `overrides` δίνεις σε κάποιο κομμάτι συγκεκριμένο αριθμό ή `keep: true`.
- `legs`: regex που βγάζει το πόδι από το όνομα (`LegFL` → `FL`, `_F` → `F`).

## Στο site (three.js)

Κάθε εξάρτημα είναι ένας κόμβος με `userData`:

```js
{ label, freecadName, subsystem, subsystemLabel, leg, geometry, triangles }
```

```js
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';

const draco = new DRACOLoader().setDecoderPath('/draco/');   // ή useGLTF του drei
const gltf = await new GLTFLoader().setDRACOLoader(draco).loadAsync('/models/spot.glb');

// Εξαρτήματα με πολλά υλικά (π.χ. servo) είναι Group με παιδιά-Mesh:
// στο κλικ, ανέβα στους γονείς μέχρι να βρεις userData.label.
function partOf(obj) { while (obj && !obj.userData.label) obj = obj.parent; return obj; }
```

## Περιορισμοί

- Link arrays (ElementCount > 0) δεν υποστηρίζονται. Το script γράφει προειδοποίηση.
- Ίδια γεωμετρία μοιράζεται και το ίδιο υλικό (π.χ. δεν γίνεται ένα πέλμα κόκκινο και τα άλλα γκρι).
- Η ιεραρχία είναι επίπεδη (`Spot` → εξαρτήματα). Για να κινούνται τα πόδια θα χρειαστούμε αργότερα
  άξονες αρθρώσεων.

## Απαιτήσεις

`freecad.cmd` (`sudo snap install freecad`) και `blender` (`sudo snap install blender --classic`).
Δοκιμασμένο με FreeCAD 1.1.4 και Blender 5.3.
