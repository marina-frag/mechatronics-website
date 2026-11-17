import { site } from '../../content/site';
import { electronics, spotGoals, spotIntro, spotTeam } from '../../content/spot/story';
import { ElectronicsDiagram } from './ElectronicsDiagram';
import { Explorer } from './Explorer';
import { AssemblyFigure, LegFigure, MotorsFigure } from './Figures';
import { ScrollHero } from './ScrollHero';

export default function SpotPage() {
  return (
    <article className="spot">
      <ScrollHero />

      <section className="section">
        <div className="prose">
          <p className="eyebrow">Ο σκοπός</p>
          <h2>Από ένα ανοιχτό σχέδιο σε ρομπότ που περπατά</h2>
          {spotIntro.aim.map((p) => (
            <p key={p}>{p}</p>
          ))}
          <ol className="goals">
            {spotGoals.map((g) => (
              <li key={g.title}>
                <strong>{g.title}</strong>
                <span>{g.text}</span>
              </li>
            ))}
          </ol>
          <dl className="facts">
            <div>
              <dt>Ομάδα</dt>
              <dd>{spotTeam.name}</dd>
            </div>
            <div>
              <dt>Ακαδημαϊκό έτος</dt>
              <dd>{spotTeam.year}</dd>
            </div>
            <div>
              <dt>Βασισμένο σε</dt>
              <dd>{spotIntro.basedOn}</dd>
            </div>
          </dl>
        </div>
      </section>

      <section className="section section--tinted" id="explore">
        <div className="container container--wide">
          <p className="eyebrow">Ελεύθερη εξερεύνηση</p>
          <h2>Εξερεύνησε το Spot</h2>
          <Explorer />
        </div>
      </section>

      <section className="section">
        <div className="prose">
          <p className="eyebrow">Ανατομία</p>
          <h2>Ένα πόδι, κομμάτι-κομμάτι</h2>
          <p>
            Κάθε πόδι είναι μια αλυσίδα: ο <strong>ώμος</strong> δένει στο σώμα, ακολουθεί ο <strong>μηρός</strong>, μετά η{' '}
            <strong>κνήμη</strong> και στο τέλος το <strong>πέλμα</strong>. Ανάμεσά τους υπάρχουν τρεις αρθρώσεις (ώμος,
            ισχίο, γόνατο) και καθεμία κινείται από τον δικό της σερβοκινητήρα.
          </p>
          <p>
            Τα κομμάτια που λέγονται «L» και «R» είναι κατοπτρικά: το αριστερό και το δεξί πόδι δεν είναι ίδια, αλλά
            είδωλα το ένα του άλλου.
          </p>
        </div>
        <div className="container">
          <LegFigure />
        </div>
      </section>

      <section className="section">
        <div className="prose">
          <p className="eyebrow">Συναρμολόγηση</p>
          <h2>Πώς δένει το ρομπότ</h2>
          <p>
            Η συναρμολόγηση πάει από μέσα προς τα έξω: πρώτα το σώμα, μετά οι ώμοι και οι κινητήρες, και στο τέλος τα
            πόδια. Πάτα αναπαραγωγή ή διάλεξε ένα βήμα.
          </p>
        </div>
        <div className="container">
          <AssemblyFigure />
        </div>
      </section>

      <section className="section">
        <div className="prose">
          <p className="eyebrow">Κίνηση</p>
          <h2>Δώδεκα κινητήρες</h2>
          <p>
            Ο σερβοκινητήρας είναι ένας μικρός κινητήρας με ενσωματωμένο μειωτήρα και αισθητήρα θέσης: δέχεται μια
            εντολή γωνίας και κρατά την άρθρωση σε αυτή. Με τρεις ανά πόδι, το Spot έχει 12 βαθμούς ελευθερίας,
            αρκετούς για να στέκεται, να γέρνει και να περπατά.
          </p>
          <p>
            Οι κινητήρες του Spot είναι <strong>ST3020</strong>, σερβοκινητήρες σειριακού bus: αντί για ένα καλώδιο
            σήματος ο καθένας, όλοι κρέμονται στην ίδια γραμμή δεδομένων και ο καθένας απαντά στο δικό του ID. Επιπλέον
            επιστρέφουν τη θέση τους, έτσι το λογισμικό ξέρει πού βρίσκεται κάθε άρθρωση.
          </p>
          <p>
            Στις αρθρώσεις, ρουλεμάν παραλαμβάνουν τα φορτία του σώματος, ώστε να μην τα σηκώνει μόνος του ο άξονας κάθε
            κινητήρα.
          </p>
        </div>
        <div className="container">
          <MotorsFigure />
        </div>
      </section>

      <section className="section">
        <div className="prose">
          <p className="eyebrow">Ηλεκτρονικά</p>
          <h2>Ο εγκέφαλος και η ενέργεια</h2>
          <p>
            Ένα Raspberry Pi 5 τρέχει το λογισμικό στάσης και βάδισης. Παίρνει τον προσανατολισμό του σώματος από το IMU,
            «βλέπει» τα εμπόδια με το LiDAR και στέλνει τις γωνίες των αρθρώσεων στους κινητήρες μέσω του σειριακού bus.
            Η ισχύς έρχεται από μπαταρίες LiPo.
          </p>
        </div>
        <div className="container">
          <ElectronicsDiagram />
        </div>
        <div className="prose">
          <ul className="component-list">
            {electronics.map((e) => (
              <li key={e.name}>
                <strong>{e.name}</strong>
                <span>{e.role}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="section section--tinted">
        <div className="prose">
          <p className="eyebrow">Η ομάδα</p>
          <h2>{spotTeam.name}</h2>
          <ul className="team">
            {spotTeam.members.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
          <p className="muted">
            {site.course} · {site.school}, {site.university} · {spotTeam.year}
          </p>
        </div>
      </section>
    </article>
  );
}
