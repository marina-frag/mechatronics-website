type Box = { id: string; x: number; y: number; w: number; h: number; title: string; sub?: string };

const BOXES: Box[] = [
  { id: 'battery', x: 20, y: 30, w: 170, h: 56, title: 'Μπαταρίες LiPo', sub: '2 × 2S 7,4 V' },
  { id: 'hub', x: 270, y: 30, w: 170, h: 56, title: 'Διανομή ισχύος', sub: '20 A ανά πόδι' },
  { id: 'stepdown', x: 270, y: 116, w: 170, h: 56, title: 'Step-down', sub: '5 V / 8 A' },
  { id: 'servos', x: 600, y: 116, w: 170, h: 56, title: '12 × ST3020', sub: 'σειριακό bus, 3 ανά πόδι' },
  { id: 'lidar', x: 20, y: 216, w: 170, h: 56, title: 'LiDAR', sub: 'RPLiDAR C1' },
  { id: 'imu', x: 20, y: 290, w: 170, h: 56, title: 'IMU', sub: 'BNO055 + BMP280' },
  { id: 'pi', x: 270, y: 252, w: 170, h: 56, title: 'Raspberry Pi 5', sub: 'υπολογιστής' },
  { id: 'bus', x: 470, y: 252, w: 110, h: 56, title: 'Οδηγός bus', sub: 'UART' },
];

const box = (id: string) => BOXES.find((b) => b.id === id)!;
const right = (b: Box) => [b.x + b.w, b.y + b.h / 2] as const;
const left = (b: Box) => [b.x, b.y + b.h / 2] as const;

type Wire = { d: string; kind: 'power' | 'signal'; both?: boolean };

function wires(): Wire[] {
  const [bx, by] = right(box('battery'));
  const hub = box('hub');
  const sd = box('stepdown');
  const sv = box('servos');
  const pi = box('pi');
  const bus = box('bus');
  return [
    { kind: 'power', d: `M${bx},${by} H${hub.x}` },
    { kind: 'power', d: `M${bx - 40},${by + 28} V${sd.y + sd.h / 2} H${sd.x}` },
    { kind: 'power', d: `M${hub.x + hub.w},${hub.y + hub.h / 2} H${sv.x + 60} V${sv.y}` },
    { kind: 'power', d: `M${sd.x + sd.w / 2},${sd.y + sd.h} V${pi.y}` },
    { kind: 'signal', d: `M${right(box('lidar')).join(',')} H${pi.x - 30} V${pi.y + 18} H${pi.x}` },
    { kind: 'signal', d: `M${right(box('imu')).join(',')} H${pi.x - 30} V${pi.y + 38} H${pi.x}` },
    { kind: 'signal', d: `M${right(pi).join(',')} H${left(bus)[0]}`, both: true },
    // Ο σειριακός bus είναι αμφίδρομος: εντολές προς τους κινητήρες, θέση πίσω.
    { kind: 'signal', d: `M${bus.x + bus.w},${bus.y + bus.h / 2} H${sv.x + 110} V${sv.y + sv.h}`, both: true },
  ];
}

/** Απλοποιημένη αρχιτεκτονική ισχύος και σημάτων. */
export function ElectronicsDiagram() {
  return (
    <figure className="figure">
      <div className="diagram-scroll">
        <svg className="diagram" viewBox="0 0 790 370" role="img" aria-labelledby="elec-title elec-desc">
          <title id="elec-title">Αρχιτεκτονική ηλεκτρονικών του Spot</title>
          <desc id="elec-desc">
            Οι μπαταρίες τροφοδοτούν τους κινητήρες μέσω της διανομής ισχύος και το Raspberry Pi μέσω του step-down.
            Το LiDAR και το IMU στέλνουν δεδομένα στο Raspberry Pi. Το Raspberry Pi μιλά με τους 12 σερβοκινητήρες
            ST3020 μέσω ενός οδηγού σειριακού bus: στέλνει εντολές θέσης και διαβάζει πίσω τη θέση τους.
          </desc>
          <defs>
            <marker id="arrow-power" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0,0 L10,5 L0,10 z" className="diagram__head--power" />
            </marker>
            <marker
              id="arrow-signal"
              viewBox="0 0 10 10"
              refX="9"
              refY="5"
              markerWidth="7"
              markerHeight="7"
              orient="auto-start-reverse"
            >
              <path d="M0,0 L10,5 L0,10 z" className="diagram__head--signal" />
            </marker>
          </defs>
          {wires().map((w, i) => (
            <path
              key={i}
              d={w.d}
              className={`diagram__wire diagram__wire--${w.kind}`}
              markerEnd={`url(#arrow-${w.kind})`}
              markerStart={w.both ? `url(#arrow-${w.kind})` : undefined}
            />
          ))}
          {BOXES.map((b) => (
            <g key={b.id}>
              <rect x={b.x} y={b.y} width={b.w} height={b.h} rx="10" className="diagram__box" />
              <text x={b.x + 14} y={b.y + 24} className="diagram__title">
                {b.title}
              </text>
              {b.sub && (
                <text x={b.x + 14} y={b.y + 43} className="diagram__sub">
                  {b.sub}
                </text>
              )}
            </g>
          ))}
        </svg>
      </div>
      <figcaption>
        <span className="legend legend--power">Ισχύς</span>
        <span className="legend legend--signal">Δεδομένα και εντολές</span>
        Απλοποιημένη αρχιτεκτονική, από τη λίστα υλικών (BOM) της ομάδας, με σερβοκινητήρες ST3020.
      </figcaption>
    </figure>
  );
}
