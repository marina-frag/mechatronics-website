# Σχέδιο: γενικό πρότυπο σελίδας project

**Κατάσταση:** πρόταση, δεν έχει υλοποιηθεί. Ο οδηγός για τις ομάδες είναι στο
[new-project-guide.md](new-project-guide.md).

## Στόχος

Μια νέα ομάδα να μπαίνει στο site χωρίς να γράψει React: στέλνει κείμενα, εικόνες και, αν θέλει, το CAD της,
και η σελίδα της στήνεται μόνη της. Το Spot κρατά τη δική του, πλουσιότερη σελίδα, αλλά πάνω στα ίδια
κοινά κομμάτια.

## Τι υπάρχει σήμερα

| Κομμάτι | Αρχεία | Γενικό; |
|---|---|---|
| Κάρτες, φίλτρα στην αρχική | `src/content/projects.ts`, `src/pages/HomePage.tsx` | Ναι |
| Σελίδα project | `src/pages/spot/*` (ScrollHero, Explorer, Figures, BodyFigure, ElectronicsDiagram) | Όχι: κείμενα και σχήματα του Spot |
| Περιεχόμενο | `src/content/spot/story.ts`, `src/content/spot/parts.ts` | Όχι |
| Route | `src/main.tsx`: μόνο `projects/spot` | Όχι |
| Φόρτωση 3D | `src/three/spotModel.ts`: `SPOT_MODEL_URL`, `useSpotModel()`, `partInfo` του Spot | Όχι |
| 3D components | `ModelStage`, `SpotModel`, `Turntable`, `Callouts` | Σχεδόν: παίρνουν το μοντέλο από το `useSpotModel()` |
| Εξερεύνηση, κάρτα εξαρτήματος | `Explorer.tsx`, `components/PartDetails.tsx` | Όχι: `LEGS`, `assemblySteps`, `partInfo` του Spot |
| Pipeline 3D | `pipeline/build_glb.sh`, `blender_build_glb.py`, `spot_parts.json` | Εν μέρει: δέχεται κάθε FCStd, αλλά γράφει πάντα `spot.glb` |
| Αυτόματη συναρμολόγηση | `tools/assembly/*` | Όχι: ειδική για τα servo του Spot. Μένει όπως είναι. |

## Πρόταση

### 1. Περιεχόμενο: ένας φάκελος ανά project

```
src/content/projects/<slug>/
├── project.md          frontmatter (στοιχεία κάρτας) + ενότητες σελίδας
└── (τίποτα άλλο)
public/projects/<slug>/
├── cover.jpg
└── images/…
public/models/<slug>.glb    αν υπάρχει 3D μοντέλο
pipeline/projects/<slug>.json   ρυθμίσεις pipeline (προαιρετικές· αλλιώς οι γενικές)
```

**Μορφή: Markdown με frontmatter**, όπως στον οδηγό. Οι φοιτητές γράφουν Markdown χωρίς να ξέρουν
TypeScript, και ένα αρχείο ανά project κρατά όλη την ομάδα σε ένα σημείο.

- **Frontmatter**: `slug`, `title`, `subtitle`, `team`, `year`, `categories`, `tags`, `summary`, `cover`,
  `coverAlt`, `members`, και τα προαιρετικά `basedOn`, `model`, `links`, `featured`.
- **Σώμα**: κάθε `##` είναι ενότητα. Τέσσερις τίτλοι έχουν ειδική σημασία:
  - `Στόχοι`: λίστα με `**τίτλο**: κείμενο` → κάρτες στόχων, όπως στο Spot;
  - `Εικόνες`: γραμμές `αρχείο | λεζάντα` → gallery;
  - `Ηλεκτρονικά`: λίστα με `**όνομα**: ρόλο` → component-list;
  - `Εξαρτήματα`: πίνακας `Label | Όνομα | Περιγραφή` → περιγραφές για την εξερεύνηση 3D.

  Όλοι οι υπόλοιποι τίτλοι γίνονται κείμενο, με τη σειρά τους.

**Ανάγνωση στο build, όχι στον browser.** Ένα μικρό Vite plugin (`vite-plugin-projects`) διαβάζει τα
`project.md`, τα ελέγχει και τα δίνει στο site ως JSON (frontmatter + ενότητες σε HTML). Έτσι ο parser
(`yaml` και `marked`, μόνο ως devDependencies) δεν φτάνει στον επισκέπτη, και τα λάθη φαίνονται στο
`npm run dev`/`build`, όχι στη σελίδα.

Το `src/content/projects.ts` παύει να γράφεται με το χέρι: οι κάρτες βγαίνουν από τα frontmatter.
Το Spot παίρνει κι αυτό ένα `project.md` για την κάρτα του, με `customPage: true`.

### 2. Σελίδα: `ProjectPage`

- **Route.** `projects/:slug` → `ProjectPage`. Το `projects/spot` μένει πρώτο, με τη δική του σελίδα.
  Άγνωστο slug → `NotFoundPage`.
- **Διάταξη**, από πάνω προς τα κάτω (κάθε μπλοκ εμφανίζεται μόνο αν έχει περιεχόμενο):
  1. **Hero**: τίτλος, υπότιτλος. Δεξιά, το 3D μοντέλο να γυρίζει (`Turntable`) ή, χωρίς μοντέλο, το `cover`.
  2. **Σκοπός** και **Στόχοι**.
  3. **Ελεύθερες ενότητες**, σε `.prose`.
  4. **Εξερεύνηση 3D**: ο σημερινός `Explorer`, γενικός.
  5. **Εικόνες**: gallery με λεζάντες και `loading="lazy"`.
  6. **Ηλεκτρονικά**: η λίστα `component-list` που υπάρχει ήδη.
  7. **Ομάδα** και **links**.
- **Φόρτωση.** Το `ProjectPage` φορτώνεται lazy, όπως σήμερα το `SpotPage`. Το three.js (~1 MB) φορτώνεται
  μόνο αν το project έχει μοντέλο: το μπλοκ 3D είναι ξεχωριστό lazy component.
- **Στυλ.** Οι υπάρχουσες κλάσεις (`section`, `prose`, `goals`, `component-list`, `team`, `figure`),
  ώστε όλα τα projects να μοιάζουν μεταξύ τους.

### 3. 3D για κάθε project

| Σήμερα | Μετά |
|---|---|
| `spotModel.ts`, `useSpotModel()` | `partsModel.ts`, `usePartsModel(url, partsConfig)` |
| `SpotModel.tsx` | `PartsModel.tsx` (ίδιος κώδικας) |
| `SPOT_MODEL_URL` σε module scope + `preload` | URL ως prop του `ModelStage` (`modelUrl`), preload στη σελίδα |
| `partInfo` από `content/spot/parts.ts` | `partInfo` από τον πίνακα `## Εξαρτήματα` του project (για το Spot: το σημερινό `parts.ts`) |
| `leg` (FL/FR/BL/BR) | γενικό `group`, με ονόματα ομάδων από τις ρυθμίσεις του project (για το Spot: τα πόδια) |
| `Explorer`/`PartDetails` με `LEGS`, `assemblySteps` | παίρνουν τα groups και τα βήματα ως props· το βήμα συναρμολόγησης γίνεται προαιρετικό |

Η σελίδα του Spot αλλάζει μόνο στα imports. Τα ειδικά σχήματα της (ScrollHero, LegFigure, BodyFigure,
AssemblyFigure) μένουν δικά της.

### 4. Pipeline ανά project

```bash
npm run glb -- <slug> <αρχείο.FCStd|.step> [--budget N]
```

- **Έξοδος.** `public/models/<slug>.glb` και, αν δεν υπάρχει `cover`, `public/projects/<slug>/render.png`.
- **Ρυθμίσεις.** Από το `pipeline/projects/<slug>.json`, αν υπάρχει, αλλιώς από το γενικό
  `pipeline/default_parts.json`. Το `spot_parts.json` γίνεται `pipeline/projects/spot.json`, με το regex
  `legs` ως `groups`.
- **STEP.** Το `freecad_export.py` κάνει πρώτα `Import.insert` και μετά συνεχίζει όπως με FCStd.
- **Χωρίς ορίσματα.** Το `npm run glb` χτίζει το Spot όπως σήμερα, για να μη σπάσει η τωρινή ροή.

### 5. Έλεγχος περιεχομένου

Ο έλεγχος τρέχει μέσα στο plugin, άρα σε κάθε `npm run dev`/`build`, και σταματά το build με καθαρό μήνυμα:

- λείπει υποχρεωτικό πεδίο ή ενότητα (`Σκοπός`, `Στόχοι`);
- `slug` όχι σε λατινικά πεζά με παύλες, ή διαφορετικό από το όνομα του φακέλου;
- εικόνα που αναφέρεται αλλά δεν υπάρχει, ή μεγαλύτερη από 400 KB (προειδοποίηση) ή 1 MB (λάθος);
- `model` χωρίς `public/models/<slug>.glb`;
- γραμμή του πίνακα `Εξαρτήματα` που δεν ταιριάζει σε κανένα Label του `.glb` (προειδοποίηση).

## Φάσεις

| Φάση | Τι | Μέγεθος | Πότε είναι έτοιμη |
|---|---|---|---|
| 1 | Plugin + `project.md` + `ProjectPage` χωρίς 3D· κάρτες από τα frontmatter | μικρό | Ένα δοκιμαστικό project (`example`) εμφανίζεται με κάρτα και σελίδα· το Spot δεν αλλάζει |
| 2 | Γενικά 3D (`partsModel`, `PartsModel`, `modelUrl`, groups)· Spot στα νέα | μεσαίο | Το Spot δουλεύει όπως πριν (hero, explorer, σχήματα, κινητό)· το `example` δείχνει μοντέλο |
| 3 | `npm run glb -- <slug>`, ρυθμίσεις ανά project, είσοδος STEP | μικρό–μεσαίο | Ένα STEP και ένα FCStd χτίζονται σε δικά τους `.glb` |
| 4 | Έλεγχος περιεχομένου, ενημέρωση README και οδηγού | μικρό | Ένα σκόπιμα λάθος `project.md` σταματά το build με σαφές μήνυμα |

Μετά τη φάση 1 μια ομάδα χωρίς 3D μπορεί ήδη να μπει. Το 3D έρχεται με τις φάσεις 2–3.

## Αποφάσεις που χρειάζονται

1. **Μορφή περιεχομένου.** Markdown με frontmatter (πρόταση) ή TypeScript, όπως σήμερα. Το TypeScript
   ελέγχεται πιο αυστηρά, αλλά δεν το γράφουν εύκολα οι φοιτητές.
2. **Ποιος τρέχει το pipeline.** Ένας συντηρητής για όλους (πρόταση: χρειάζεται Linux, FreeCAD και Blender)
   ή κάθε ομάδα μόνη της.
3. **Πώς στέλνουν οι ομάδες.** Zip ή link στον συντηρητή (πρόταση, για αρχή) ή pull request στο GitHub,
   αν το repo γίνει κοινό.
4. **Δημοσιότητα αρχείων.** Αν τα CAD και τα STL είναι διαθέσιμα για κατέβασμα ή μόνο το 3D μοντέλο.
5. **Ονόματα φοιτητών.** Αν θα φαίνονται ονόματα και με ποια συναίνεση. Αριθμοί μητρώου ποτέ.

## Κίνδυνοι

- **Βάρος σελίδας.** Πολλά μοντέλα και φωτογραφίες. Μετριάζεται με triangle budget ανά μοντέλο
  (σήμερα 400k → ~1 MB `.glb`), όρια στις εικόνες και lazy φόρτωση.
- **Παλινδρόμηση στο Spot** στη φάση 2. Πριν το merge, έλεγχος όλων των σχημάτων του Spot σε desktop και κινητό.
- **Labels με ελληνικά γράμματα** στα CAD των ομάδων (συνέβη στο Spot). Ο έλεγχος της φάσης 4 τα εντοπίζει.
