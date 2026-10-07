const COLORS = {
  dark_gray: '#4a4f55',
  light_gray: '#aab0b5',
  black: '#202226',
  beige: '#c7ad85',
}

export default function RampDiagram({ ramp }) {
  const left = 55
  const bottom = 245
  const maxWidth = 480
  const maxHeight = 180
  const scale = Math.min(maxWidth / ramp.horizontal_run_cm, maxHeight / ramp.height_cm)
  const run = ramp.horizontal_run_cm * scale
  const rise = ramp.height_cm * scale
  const topX = left + run
  const topY = bottom - rise
  const ux = run / ramp.ramp_length_cm
  const uy = -rise / ramp.ramp_length_cm
  const nx = -uy
  const ny = ux

  return (
    <figure className="diagram-card">
      <figcaption>Схема пандуса сбоку</figcaption>
      <svg viewBox="0 0 600 300" role="img" aria-label="Схема рассчитанного пандуса">
        <line x1="28" y1={bottom} x2="570" y2={bottom} className="floor" />
        <polygon points={`${left},${bottom} ${topX},${topY} ${topX},${bottom}`} fill={`${COLORS[ramp.color]}22`} />
        <line x1={left} y1={bottom} x2={topX} y2={topY} stroke={COLORS[ramp.color]} className="ramp-line" />
        <line x1={topX} y1={topY} x2={topX} y2={bottom} className="measure" />
        {ramp.step_positions_cm.map((position) => {
          const x = left + ux * position * scale
          const y = bottom + uy * position * scale
          return <line key={position} x1={x - nx * 7} y1={y - ny * 7} x2={x + nx * 7} y2={y + ny * 7} className="step" />
        })}
        <text x={topX + 10} y={(topY + bottom) / 2}>h = {ramp.height_cm} см</text>
        <text x={(left + topX) / 2} y={bottom + 27} textAnchor="middle">проекция {ramp.horizontal_run_cm} см</text>
        <text x={(left + topX) / 2 - 15} y={(bottom + topY) / 2 - 16} textAnchor="middle">{ramp.ramp_length_cm} см</text>
      </svg>
      <p>Схема показывает расчётные пропорции. Конструкция основания пока не определена.</p>
    </figure>
  )
}

