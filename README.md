# Μηχατρονικά συστήματα: projects

Εκπαιδευτική πλατφόρμα για το μάθημα «Σχεδιασμός και ανάπτυξη μηχατρονικών συστημάτων»
(ΣΗΜΜΥ ΕΜΠ). Πρώτο project: **Spot**. React + Vite + TypeScript + three.js.

## Εκκίνηση

Χρειάζεται Node.js ≥ 20.19 (με nvm: `nvm use`, διαβάζει το `.nvmrc`).

```bash
npm install      # μία φορά
npm run dev      # http://localhost:5173, ανανεώνεται μόνο του σε κάθε αλλαγή
```

## Ενημέρωση του 3D μοντέλου

Αποθήκευσε τη συναρμολόγηση στο FreeCAD και τρέξε:

```bash
npm run glb
```

Γράφει το `public/models/spot.glb` και την εικόνα της κάρτας `public/projects/spot/render.png`.
Λεπτομέρειες στο [pipeline/README.md](pipeline/README.md).

## Πού αλλάζει το περιεχόμενο

| Τι | Αρχείο |
|---|---|
| Στοιχεία μαθήματος | `src/content/site.ts` |
| Λίστα projects (κάρτες, φίλτρα) | `src/content/projects.ts` |
| Διαλέξεις | `src/content/material.ts` + PDF στο `public/material/` |
| Ονόματα και περιγραφές εξαρτημάτων | `src/content/spot/parts.ts` |
| Κείμενα σελίδας Spot, βήματα συναρμολόγησης, ηλεκτρονικά, ομάδα | `src/content/spot/story.ts` |

## Νέα ομάδα

Τι στέλνει μια ομάδα για να μπει το project της: [docs/new-project-guide.md](docs/new-project-guide.md).
Σχέδιο για το γενικό πρότυπο σελίδας: [docs/project-template-plan.md](docs/project-template-plan.md).

## Δημοσίευση

```bash
npm run build    # στατικά αρχεία στο dist/
npm run preview  # έλεγχος του build τοπικά
```

Το `dist/` είναι σκέτα αρχεία (HTML, JS, CSS, `.glb`): δεν χρειάζεται server ή βάση
δεδομένων, και ανεβαίνει σε οποιαδήποτε στατική φιλοξενία (Netlify, Cloudflare Pages, Vercel,
GitHub Pages ή server της σχολής). Για φιλοξενία σε υποφάκελο, π.χ. στο GitHub Pages:
`BASE_PATH=/όνομα-repo/ npm run build`.

**PDF διαλέξεων.** Στο `npm run dev` φαίνονται πάντα. Στο build μπαίνουν μόνο με
`VITE_PUBLISH_SLIDES=true npm run build`, αφού δοθεί άδεια από τον διδάσκοντα. Χωρίς αυτό, η σελίδα
«Υλικό μαθήματος» δείχνει τις διαλέξεις χωρίς κουμπιά PDF, και ο φάκελος `material/` δεν μπαίνει στο `dist/`.
Τα PDF δεν είναι στο git (`.gitignore`): υπάρχουν μόνο τοπικά, στο `public/material/` και στο `class_slides/`.
Για να μπουν στο GitHub Pages όταν δοθεί άδεια, βγάλε τη γραμμή `public/material/*.pdf` από το `.gitignore`,
κάνε commit τα PDF και όρισε `PUBLISH_SLIDES=true`.

### GitHub Pages (αυτόματα σε κάθε push)

Το [.github/workflows/pages.yml](.github/workflows/pages.yml) χτίζει και ανεβάζει το site σε κάθε push στο `main`,
στο `https://<χρήστης>.github.io/<repo>/`. Μία φορά, στο GitHub:

1. Αν το repo είναι private, χρειάζεται GitHub Pro (δωρεάν με το GitHub Student Developer Pack, με email
   `@mail.ntua.gr`). Αλλιώς το repo γίνεται public.
2. **Settings → Pages → Build and deployment → Source: GitHub Actions.**
3. Push στο `main` (ή **Actions → Δημοσίευση στο GitHub Pages → Run workflow**). Η διεύθυνση φαίνεται στο
   Settings → Pages όταν τελειώσει.

Προαιρετικές μεταβλητές, στο **Settings → Secrets and variables → Actions → Variables**:

| Μεταβλητή | Τιμή | Τι κάνει |
|---|---|---|
| `PUBLISH_SLIDES` | `true` | Βάζει τα PDF των διαλέξεων στο site |
| `BASE_PATH` | `/` | Για δικό του domain (π.χ. subdomain της σχολής), αντί για τον υποφάκελο του repo |

Το 3D μοντέλο δεν χτίζεται στο GitHub (χρειάζεται FreeCAD και Blender): ανεβαίνει το
`public/models/spot.glb` όπως είναι στο repo. Μετά από `npm run glb`, κάνε commit και push το νέο `.glb`.
Έλεγχος του build για GitHub Pages τοπικά: `BASE_PATH=/mechatronics-website/ npm run build` και
`BASE_PATH=/mechatronics-website/ npm run preview`, στο `http://localhost:4173/mechatronics-website/`.

# How to run

1. Πήγαινε στον φάκελο του site:

```
cd ~/mechatronics_web
```

2. Ξεκίνα τον server:

```
npm run dev
```

Μετά άνοιξε στον browser τη διεύθυνση που θα γράψει, συνήθως **[http://localhost:5173](http://localhost:5173/)**. Ο server μένει ανοιχτός όσο είναι ανοιχτό το τερματικό. Όποια αλλαγή κάνεις στα αρχεία φαίνεται αμέσως στη σελίδα. Τον σταματάς με **Ctrl+C**.

Δύο πράγματα να ξέρεις:

- **Η θύρα 5173 είναι πιασμένη τώρα** από τον server που άνοιξα εγώ μέσα στην εφαρμογή. Αν τρέξεις τον δικό σου, το Vite θα διαλέξει μόνο του άλλη θύρα (π.χ. 5174) και θα σου γράψει ποια.
- Το `npm install` έχει ήδη γίνει. Θα το ξαναχρειαστείς μόνο αν σβηστεί ο φάκελος `node_modules` ή αν πάρεις το project σε άλλον υπολογιστή.

### Άλλες χρήσιμες εντολές (από τον ίδιο φάκελο)

Ενημέρωση του 3D μοντέλου, αφού αποθηκεύσεις στο FreeCAD:

```
npm run glb
```

Η τελική έκδοση για δημοσίευση (βγαίνει στον φάκελο `dist/`):

```
npm run build
```

Έλεγχος αυτής της τελικής έκδοσης τοπικά:

```
npm run preview
```