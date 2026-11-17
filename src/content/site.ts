export const site = {
  course: 'Σχεδιασμός και ανάπτυξη μηχατρονικών συστημάτων',
  school: 'Σχολή Ηλεκτρολόγων Μηχανικών και Μηχανικών Υπολογιστών',
  university: 'Εθνικό Μετσόβιο Πολυτεχνείο',
  universityShort: 'ΕΜΠ',
  instructor: 'Παναγιώτης Βαρθολομαίος',
};

/** URL για αρχεία του φακέλου public/, σωστό και όταν το site ζει σε υποφάκελο. */
export function asset(path: string): string {
  return `${import.meta.env.BASE_URL}${path.replace(/^\//, '')}`;
}
