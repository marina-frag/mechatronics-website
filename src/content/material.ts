export type Lecture = {
  number: string;
  title: string;
  date: string;
  topics: string[];
  pages: number;
  sizeMb: number;
  /** Διαδρομή μέσα στο public/. */
  file: string;
};

/** Τα PDF είναι στο site; Στο npm run dev πάντα· στο build μόνο με VITE_PUBLISH_SLIDES=true (βλ. vite.config.ts). */
export const slidesPublished = import.meta.env.DEV || import.meta.env.VITE_PUBLISH_SLIDES === 'true';

// Από τα PDF του φακέλου class_slides (τίτλοι και περιεχόμενα της 1ης–2ης σελίδας).
export const lectures: Lecture[] = [
  {
    number: '01',
    title: 'Εισαγωγή',
    date: '2 Οκτωβρίου 2026',
    topics: ['Εισαγωγή στα μηχατρονικά συστήματα'],
    pages: 34,
    sizeMb: 5.1,
    file: 'material/01-eisagogi.pdf',
  },
  {
    number: '02',
    title: 'Διάλεξη 2η',
    date: '2 Οκτωβρίου 2026',
    topics: ['Ενέργεια συστήματος και ροή ισχύος', 'Μηχανικά θεμελιώδη στοιχεία'],
    pages: 55,
    sizeMb: 4.9,
    file: 'material/02-dialexi.pdf',
  },
  {
    number: '03',
    title: 'Διάλεξη 3η',
    date: '2–9 Οκτωβρίου 2026',
    topics: [
      'Ηλεκτρικά, υδραυλικά και θερμικά συστήματα',
      'Γενικευμένη αναπαράσταση γραμμικών μονόθυρων στοιχείων',
    ],
    pages: 75,
    sizeMb: 2.6,
    file: 'material/03-dialexi.pdf',
  },
  {
    number: '04',
    title: 'Διάλεξη 4η',
    date: '9–16 Οκτωβρίου 2026',
    topics: ['Γραμμικοί γράφοι'],
    pages: 55,
    sizeMb: 3.6,
    file: 'material/04-dialexi.pdf',
  },
];
