const COLORS = {
  dark_gray: '#4a4f55',
  light_gray: '#aab0b5',
  black: '#202226',
  beige: '#c7ad85',
}

export default function RampDiagram({ ramp }) {
  const geometry = ramp.geometry
  const { ramp_start: A, ramp_end: B, vertical_projection: V, base_end: C, support_hinge: D, support_foot: S } = geometry.points
  const support = geometry.support
  const measurements = geometry.measurements
  const canvas = { width: 720, height: 430, left: 72, right: 76, top: 60, bottom: 100 }
  const usableWidth = canvas.width - canvas.left - canvas.right
  const usableHeight = canvas.height - canvas.top - canvas.bottom
  const scale = Math.min(usableWidth / V.x, usableHeight / B.y)
  const floorY = canvas.height - canvas.bottom
  const sx = (x) => canvas.left + x * scale
  // Backend uses Y up; SVG uses Y down, so only this display transform inverts Y.
  const sy = (y) => floorY - y * scale

  return (
    <figure className="diagram-card">
      <figcaption>Геометрический профиль пандуса</figcaption>
      <svg viewBox={`0 0 ${canvas.width} ${canvas.height}`} role="img" aria-label="Боковой профиль пандуса с основанием и опорной стойкой">
        <line x1="34" y1={floorY} x2={canvas.width - 34} y2={floorY} className="floor" />
        <line x1={sx(B.x)} y1={sy(B.y)} x2={sx(V.x)} y2={sy(V.y)} className="control-line" />
        <line x1={sx(A.x)} y1={sy(A.y)} x2={sx(C.x)} y2={sy(C.y)} className="base-line" />
        <line x1={sx(S.x)} y1={sy(S.y)} x2={sx(D.x)} y2={sy(D.y)} className="support-line" />
        <line x1={sx(A.x)} y1={sy(A.y)} x2={sx(B.x)} y2={sy(B.y)} stroke={COLORS[ramp.color]} className="ramp-line" />

        {geometry.step_points.map((rail) => (
          <line key={rail.start_distance_cm} x1={sx(rail.start.x)} y1={sy(rail.start.y)} x2={sx(rail.end.x)} y2={sy(rail.end.y)} className="side-step-band" />
        ))}

        <rect x={sx(S.x) - 18} y={floorY - 12} width="18" height="12" rx="1.5" className="support-stop" />
        <circle cx={sx(D.x)} cy={sy(D.y)} r="9" className="hinge-outer" />
        <circle cx={sx(D.x)} cy={sy(D.y)} r="3.5" className="hinge-axis" />
        <text x={sx(D.x) - 16} y={sy(D.y) - 18} textAnchor="end" className="mechanics-label">D — шарнир, 75%</text>
        <text x={sx(S.x) - 22} y={floorY - 18} textAnchor="end" className="mechanics-label">упор</text>

        <line x1={sx(C.x)} y1={floorY + 34} x2={sx(V.x)} y2={floorY + 34} className="offset-line" />
        <line x1={sx(C.x)} y1={floorY + 25} x2={sx(C.x)} y2={floorY + 43} className="dimension-cap" />
        <line x1={sx(V.x)} y1={floorY + 25} x2={sx(V.x)} y2={floorY + 43} className="dimension-cap" />
        <text x={(sx(C.x) + sx(V.x)) / 2} y={floorY + 57} textAnchor="middle">отступ {geometry.base_vertical_offset_cm} см</text>

        <text x={sx(B.x) + 12} y={(sy(B.y) + floorY) / 2}>высота {ramp.height_cm} см</text>
        <text x={(sx(A.x) + sx(D.x)) / 2 - 18} y={(sy(A.y) + sy(D.y)) / 2 - 17} textAnchor="middle">A→D {measurements.ramp_start_to_hinge_cm} см</text>
        <text x={(sx(A.x) + sx(S.x)) / 2} y={floorY + 22} textAnchor="middle">A→S {measurements.ramp_start_to_support_foot_cm} см</text>
        <text x={(sx(S.x) + sx(C.x)) / 2} y={floorY + 22} textAnchor="middle">S→C {measurements.support_foot_to_base_end_cm} см</text>
        <text x={sx(A.x) + 54} y={floorY - 12}>наклон {ramp.angle_deg}°</text>
        <text x={(sx(S.x) + sx(D.x)) / 2 + 14} y={(sy(S.y) + sy(D.y)) / 2 - 9} textAnchor="start">D→S {measurements.support_length_cm} см</text>
        <text x={(sx(S.x) + sx(D.x)) / 2 + 14} y={(sy(S.y) + sy(D.y)) / 2 + 10} textAnchor="start">{support.floor_angle_deg}° к полу</text>
        <text x={sx(S.x)} y={floorY + 43} textAnchor="middle">S — опора стойки</text>

        {[[A, 'A'], [B, 'B'], [V, 'V'], [C, 'C — конец основания']].map(([p, label]) => (
          <g key={label}><circle cx={sx(p.x)} cy={sy(p.y)} r="3.5" className="key-point" /><text x={sx(p.x) + 8} y={sy(p.y) - 8} className="point-label">{label}</text></g>
        ))}
      </svg>
      <p>Стойка находится внутри профиля: от опоры S она идёт вверх-вправо к шарниру D. Точка C обозначает только конец основания.</p>
    </figure>
  )
}

