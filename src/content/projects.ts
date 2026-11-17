export type Project = {
  slug: string;
  title: string;
  team: string;
  /** Ακαδημαϊκό έτος, π.χ. "2026–27". */
  year: string;
  categories: string[];
  tags: string[];
  summary: string;
  /** Διαδρομή μέσα στο public/. */
  cover: string;
  coverAlt: string;
  href: string;
  featured?: boolean;
};

export const projects: Project[] = [
  {
    slug: 'spot',
    title: 'Spot',
    team: 'Ομάδα Spot',
    year: '2026–27',
    categories: ['Τετράποδο ρομπότ'],
    tags: ['Τετράποδο ρομπότ', 'Έλεγχος κίνησης', 'LiDAR', '3D εκτύπωση'],
    summary:
      'Ρομποτικός τετράποδος σκύλος βασισμένος στο ανοιχτό σχέδιο SpotMicro: 3D εκτυπωμένος σκελετός, 12 σερβοκινητήρες, βάδιση με τηλεχειρισμό και αποφυγή εμποδίων με LiDAR.',
    cover: 'projects/spot/render.png',
    coverAlt: 'Τα εξαρτήματα του Spot από το αρχείο CAD της ομάδας',
    href: '/projects/spot',
    featured: true,
  },
];
