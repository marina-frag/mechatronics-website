import { lectures } from '../content/material';
import { asset, site } from '../content/site';

export function MaterialPage() {
  return (
    <section className="section section--first">
      <div className="container">
        <p className="eyebrow">{site.course}</p>
        <h1>Υλικό μαθήματος</h1>
        <p className="lead">
          Οι διαφάνειες των διαλέξεων του {site.instructorGenitive}, {site.school}, {site.university}.
        </p>

        <ol className="lecture-list">
          {lectures.map((l) => (
            <li key={l.file} className="lecture">
              <span className="lecture__number" aria-hidden="true">
                {l.number}
              </span>
              <div className="lecture__body">
                <h2>{l.title}</h2>
                <p className="muted">
                  {l.date} · {l.pages} σελίδες
                </p>
                <ul className="lecture__topics">
                  {l.topics.map((t) => (
                    <li key={t}>{t}</li>
                  ))}
                </ul>
              </div>
              <a className="btn" href={asset(l.file)} target="_blank" rel="noopener">
                PDF · {l.sizeMb.toLocaleString('el-GR')} MB
              </a>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
