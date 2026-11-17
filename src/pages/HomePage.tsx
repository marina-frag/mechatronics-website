import { Suspense, lazy, useMemo, useState } from 'react';
import { Link } from 'react-router';
import { Segmented } from '../components/Controls';
import { projects, type Project } from '../content/projects';
import { asset, site } from '../content/site';

const FeaturedModel = lazy(() => import('./FeaturedModel'));

const ALL = 'all';

export function HomePage() {
  const featured = projects.find((p) => p.featured) ?? projects[0];
  return (
    <>
      <section className="home-hero">
        <div className="container">
          <p className="eyebrow">
            {site.school} · {site.universityShort}
          </p>
          <h1 className="display">Το μάθημα μέσα από τις κατασκευές</h1>
          <p className="lead">
            Τα projects του μαθήματος «{site.course}», με τα πραγματικά 3D μοντέλα και αρχεία των ομάδων.
          </p>
        </div>

        <div className="container container--wide">
          <div className="feature">
            <div className="feature__visual">
              <Suspense fallback={null}>
                <FeaturedModel />
              </Suspense>
            </div>
            <div className="feature__caption">
              <p className="eyebrow">Επιλεγμένο project</p>
              <h2>
                <Link to={featured.href}>{featured.title}</Link>
              </h2>
              <p>{featured.summary}</p>
              <div className="actions">
                <a className="btn btn--primary" href="#projects">
                  Εξερεύνησε τα projects
                </a>
                <Link className="btn" to="/material">
                  Υλικό μαθήματος
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      <ProjectsSection />
    </>
  );
}

function ProjectsSection() {
  const [year, setYear] = useState(ALL);
  const [category, setCategory] = useState(ALL);

  const years = useMemo(() => [...new Set(projects.map((p) => p.year))].sort().reverse(), []);
  const categories = useMemo(() => [...new Set(projects.flatMap((p) => p.categories))].sort(), []);
  const shown = projects.filter(
    (p) => (year === ALL || p.year === year) && (category === ALL || p.categories.includes(category)),
  );

  return (
    <section id="projects" className="section">
      <div className="container container--wide">
        <div className="section__head">
          <h2>Projects</h2>
          <div className="filters">
            <div className="filter">
              <span className="filter__label">Ακαδημαϊκό έτος</span>
              <Segmented
                label="Φίλτρο ακαδημαϊκού έτους"
                value={year}
                onChange={setYear}
                options={[{ value: ALL, label: 'Όλα' }, ...years.map((y) => ({ value: y, label: y }))]}
              />
            </div>
            <div className="filter">
              <span className="filter__label">Κατηγορία</span>
              <Segmented
                label="Φίλτρο κατηγορίας"
                value={category}
                onChange={setCategory}
                options={[{ value: ALL, label: 'Όλες' }, ...categories.map((c) => ({ value: c, label: c }))]}
              />
            </div>
          </div>
        </div>

        {shown.length ? (
          <ul className="project-grid">
            {shown.map((p) => (
              <li key={p.slug}>
                <ProjectCard project={p} />
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">Δεν υπάρχουν projects με αυτά τα φίλτρα.</p>
        )}
      </div>
    </section>
  );
}

function ProjectCard({ project }: { project: Project }) {
  return (
    <article className="project-card">
      <Link to={project.href} className="project-card__link">
        <div className="project-card__media">
          <img src={asset(project.cover)} alt={project.coverAlt} loading="lazy" />
        </div>
        <div className="project-card__body">
          <p className="eyebrow">
            {project.team} · {project.year}
          </p>
          <h3>{project.title}</h3>
          <p>{project.summary}</p>
          <ul className="tags" aria-label="Ετικέτες">
            {project.tags.map((t) => (
              <li key={t}>{t}</li>
            ))}
          </ul>
        </div>
      </Link>
    </article>
  );
}
