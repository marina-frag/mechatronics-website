/**
 * Περιγραφές εξαρτημάτων του Spot. Το site αναγνωρίζει κάθε κομμάτι από το
 * Label του στο FreeCAD (π.χ. "foot_LegBL") με τους κανόνες match παρακάτω.
 * Ο πρώτος κανόνας που ταιριάζει κερδίζει, οπότε τα πιο ειδικά μπαίνουν πρώτα.
 */

export type SubsystemKey = 'frame' | 'motors' | 'electronics';

export const SUBSYSTEMS: Record<SubsystemKey, { label: string; plural: string }> = {
  frame: { label: 'Σκελετός', plural: 'κομμάτια σκελετού' },
  motors: { label: 'Κινητήρες', plural: 'κινητήρες' },
  electronics: { label: 'Ηλεκτρονικά', plural: 'ηλεκτρονικά' },
};

export const SUBSYSTEM_ORDER: SubsystemKey[] = ['frame', 'motors', 'electronics'];

export const LEGS: Record<string, { label: string; short: string }> = {
  FL: { label: 'Μπροστινό αριστερό πόδι', short: 'ΜΑ' },
  FR: { label: 'Μπροστινό δεξί πόδι', short: 'ΜΔ' },
  BL: { label: 'Πίσω αριστερό πόδι', short: 'ΠΑ' },
  BR: { label: 'Πίσω δεξί πόδι', short: 'ΠΔ' },
  F: { label: 'Μπροστινό ζεύγος ποδιών', short: 'Μ' },
  B: { label: 'Πίσω ζεύγος ποδιών', short: 'Π' },
};

export const LEG_ORDER = ['FL', 'FR', 'BL', 'BR', 'F', 'B', ''];

export type PartTypeKey =
  | 'body'
  | 'shoulder'
  | 'reinforcement'
  | 'motor'
  | 'bearing'
  | 'thigh'
  | 'thigh_joint'
  | 'thigh_cover'
  | 'shin'
  | 'foot'
  | 'other';

type PartType = { key: PartTypeKey; match: RegExp; title: string; description: string };

const PART_TYPES: PartType[] = [
  {
    key: 'thigh_cover',
    match: /arm_cover/i,
    title: 'Κάλυμμα μηρού',
    description: 'Κάλυμμα του άνω τμήματος του ποδιού, προσαρμοσμένο στην ενίσχυση του ώμου.',
  },
  {
    key: 'thigh_joint',
    match: /arm_joint/i,
    title: 'Σύνδεσμος μηρού',
    description: 'Συνδέει τον μηρό με την ενίσχυση του ώμου.',
  },
  {
    key: 'reinforcement',
    match: /shoulder_reinforcement/i,
    title: 'Ενίσχυση ώμου',
    description:
      'Ενισχύει την άρθρωση του ώμου. Η έκδοση «st» είναι προσαρμοσμένη από την ομάδα στους σερβοκινητήρες του Spot.',
  },
  {
    key: 'shoulder',
    match: /^I_shoulder/i,
    title: 'Εσωτερικός ώμος',
    description:
      'Ο ώμος δένει ένα ζεύγος ποδιών (μπροστά ή πίσω) με το σώμα. Αποτελείται από ένα εσωτερικό και ένα εξωτερικό τμήμα.',
  },
  {
    key: 'shoulder',
    match: /^O_shoulder/i,
    title: 'Εξωτερικός ώμος',
    description:
      'Ο ώμος δένει ένα ζεύγος ποδιών (μπροστά ή πίσω) με το σώμα. Αποτελείται από ένα εσωτερικό και ένα εξωτερικό τμήμα.',
  },
  {
    key: 'thigh',
    match: /(^|_)arm_st/i,
    title: 'Μηρός',
    description:
      'Το άνω τμήμα του ποδιού, ανάμεσα στον ώμο και το γόνατο. Υπάρχει σε αριστερή (L) και δεξιά (R) έκδοση, κατοπτρικές μεταξύ τους.',
  },
  {
    key: 'shin',
    match: /wrist/i,
    title: 'Κνήμη',
    description: 'Το κάτω τμήμα του ποδιού. Περιστρέφεται στο γόνατο και καταλήγει στο πέλμα.',
  },
  {
    key: 'foot',
    match: /foot/i,
    title: 'Πέλμα',
    description: 'Το σημείο όπου το πόδι πατά στο έδαφος. Στερεώνεται στην άκρη της κνήμης.',
  },
  {
    key: 'motor',
    match: /motor|servo|st3020|scs15|scs40/i,
    title: 'Σερβοκινητήρας ST3020',
    description:
      'Σερβοκινητήρας σειριακού bus: κινεί μία άρθρωση και επιστρέφει τη θέση της στο λογισμικό. Κάθε πόδι έχει τρεις (ώμος, ισχίο, γόνατο), άρα 12 συνολικά.',
  },
  {
    key: 'bearing',
    match: /bearing|626zz|nsk/i,
    title: 'Ρουλεμάν',
    description:
      'Ρουλεμάν 626ZZ (6 × 19 × 6 mm) στον άξονα της άρθρωσης: μειώνει την τριβή και παραλαμβάνει φορτία που αλλιώς θα σήκωνε ο άξονας του κινητήρα.',
  },
  {
    key: 'body',
    match: /side_plate/i,
    title: 'Πλαϊνή πλάκα σώματος',
    description: 'Πλαϊνό τοίχωμα του σώματος.',
  },
  {
    key: 'body',
    match: /T_cover/i,
    title: 'Πάνω κάλυμμα σώματος',
    description: 'Κλείνει το σώμα από πάνω και προστατεύει τα ηλεκτρονικά.',
  },
  {
    key: 'body',
    match: /mega_B_cover/i,
    title: 'Κάτω κάλυμμα σώματος',
    description: 'Κλείνει το σώμα από κάτω.',
  },
  {
    key: 'body',
    match: /^(F_cover|L_cover)/i,
    title: 'Μπροστινό κάλυμμα',
    description: 'Κλείνει το σώμα από μπροστά.',
  },
  {
    key: 'body',
    match: /^(B_cover|R_cover)/i,
    title: 'Πίσω κάλυμμα',
    description: 'Κλείνει το σώμα από πίσω.',
  },
  {
    key: 'body',
    match: /^plate/i,
    title: 'Πλάκα ηλεκτρονικών',
    description: 'Εσωτερική πλάκα του σώματος, πάνω στην οποία στερεώνονται τα ηλεκτρονικά.',
  },
];

export type PartInfo = { key: PartTypeKey; title: string; description: string };

export function partInfo(label: string): PartInfo {
  const t = PART_TYPES.find((p) => p.match.test(label));
  return t ? { key: t.key, title: t.title, description: t.description } : { key: 'other', title: label, description: '' };
}

/** Το STL από το οποίο προήλθε το κομμάτι (στο FreeCAD το Label = όνομα αρχείου). */
export function sourceFile(label: string): string {
  return `${label}.stl`;
}
