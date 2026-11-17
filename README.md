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

## Δημοσίευση

```bash
npm run build    # στατικά αρχεία στο dist/
npm run preview  # έλεγχος του build τοπικά
```

Το `dist/` είναι σκέτα αρχεία (HTML, JS, CSS, `.glb`, PDF): δεν χρειάζεται server ή βάση
δεδομένων, και ανεβαίνει σε οποιαδήποτε στατική φιλοξενία (Netlify, Cloudflare Pages, Vercel,
GitHub Pages ή server της σχολής). Για φιλοξενία σε υποφάκελο, π.χ. στο GitHub Pages:
`BASE_PATH=/όνομα-repo/ npm run build`.

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