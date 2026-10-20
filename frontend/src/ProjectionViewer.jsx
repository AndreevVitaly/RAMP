import { useState } from 'react'
import RampDiagram from './RampDiagram'
import { COLORS } from './materials'
import { DogSilhouette } from './pets'

function frame(points, width = 700, height = 410, margin = 55) {
  const xs = points.map((p) => p[0]); const ys = points.map((p) => p[1])
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys)
  const scale = Math.min((width - margin * 2) / Math.max(maxX - minX, 1), (height - margin * 2) / Math.max(maxY - minY, 1))
  return { width, height, scale, x: (v) => margin + (v - minX) * scale, y: (v) => height - margin - (v - minY) * scale }
}

function centeredFrame(points, width = 700, height = 410, margin = 24) {
  const xs = points.map((p) => p[0]); const ys = points.map((p) => p[1])
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys)
  const contentWidth = Math.max(maxX - minX, 1); const contentHeight = Math.max(maxY - minY, 1)
  const scale = Math.min((width - margin * 2) / contentWidth, (height - margin * 2) / contentHeight)
  const offsetX = (width - contentWidth * scale) / 2
  const offsetY = (height - contentHeight * scale) / 2
  return { width, height, scale, x: (v) => offsetX + (v - minX) * scale, y: (v) => height - offsetY - (v - minY) * scale }
}

function TopView({ ramp, pet }) {
  const g = ramp.geometry_3d; const { horizontal_run_cm: run, width_cm: w } = g.dimensions
  const petX = run + (pet?.enabled ? 10 : 0)
  const f = centeredFrame([[0, 0], [run, w], [petX + (pet?.enabled ? pet.length_cm : 0), Math.max(w, pet?.height_cm || 0)]])
  return <figure className="diagram-card projection-card top-product-view"><svg viewBox="0 0 700 410" role="img" aria-label="Пандус, вид сверху">
    <polygon points={`${f.x(0)},${f.y(0)} ${f.x(run)},${f.y(0)} ${f.x(run)},${f.y(w)} ${f.x(0)},${f.y(w)}`} fill={COLORS[ramp.color]} stroke={COLORS[ramp.color]} className="projection-surface product-surface" />
    {g.steps.map((s) => <polygon key={s.start_distance_cm} points={`${f.x(s.top_start_left.x)},${f.y(s.top_start_left.y)} ${f.x(s.top_end_left.x)},${f.y(s.top_end_left.y)} ${f.x(s.top_end_right.x)},${f.y(s.top_end_right.y)} ${f.x(s.top_start_right.x)},${f.y(s.top_start_right.y)}`} fill={COLORS[ramp.color]} className="projection-step-band" />)}
    <DogSilhouette pet={pet} view="top" x={f.x(petX)} groundY={f.y(w / 2)} heightPx={f.scale * (pet?.height_cm || 0)} />
  </svg></figure>
}

function FrontView({ ramp, pet }) {
  const g = ramp.geometry_3d; const { height_cm: h, width_cm: w } = g.dimensions
  const support = g.support.corners; const base = g.base.volume_corners; const surface = g.ramp_surface.volume_corners
  const panelPoints = g.side_panels.enabled ? ['left', 'right'].flatMap((name) => [g.side_panels[name].bottom_end, g.side_panels[name].top_end].map((p) => [p.y, p.z])) : []
  const petX = w + (pet?.enabled ? 10 : 0)
  const f = frame([[0, base.bottom_c_left.z], [w, h], [petX + (pet?.enabled ? pet.front_width_cm : 0), pet?.height_cm || 0], ...panelPoints])
  return <Projection title="Вид спереди · YZ"><svg viewBox="0 0 700 410">
    <rect x={f.x(0)} y={f.y(h)} width={f.x(w) - f.x(0)} height={f.y(0) - f.y(h)} fill={COLORS[ramp.color]} className="projection-surface front-surface" />
    <rect x={f.x(0)} y={f.y(base.top_c_left.z)} width={f.x(w) - f.x(0)} height={f.y(base.bottom_c_left.z) - f.y(base.top_c_left.z)} fill={COLORS[ramp.color]} className="projection-base front-base" />
    <polygon points={`${f.x(support.foot_left_front.y)},${f.y(support.foot_left_front.z)} ${f.x(support.foot_right_front.y)},${f.y(support.foot_right_front.z)} ${f.x(support.hinge_right_front.y)},${f.y(support.hinge_right_front.z)} ${f.x(support.hinge_left_front.y)},${f.y(support.hinge_left_front.z)}`} fill={COLORS[ramp.color]} className="front-support-panel" />
    <rect x={f.x(0)} y={f.y(surface.top_b_left.z)} width={f.x(w) - f.x(0)} height={f.y(surface.bottom_b_left.z) - f.y(surface.top_b_left.z)} fill={COLORS[ramp.color]} className="projection-surface front-surface" />
    {g.side_panels.enabled && ['left', 'right'].map((name) => {
      const panel = g.side_panels[name]
      return <line key={name} x1={f.x(panel.top_end.y)} y1={f.y(panel.top_end.z)} x2={f.x(panel.bottom_end.y)} y2={f.y(panel.bottom_end.z)} stroke={COLORS[ramp.color]} className="front-side-panel" />
    })}
    <DogSilhouette pet={pet} view="front" x={f.x(petX)} groundY={f.y(0)} heightPx={f.scale * (pet?.height_cm || 0)} />
    <text x={f.x(w / 2)} y={f.y(0) + 28} textAnchor="middle">ширина {w} см</text>
    <text x={f.x(w) + 12} y={f.y(h / 2)}>высота {h} см</text>
  </svg></Projection>
}

function AxonometricView({ ramp, pet }) {
  const g = ramp.geometry_3d; const surface = g.ramp_surface.volume_corners; const base = g.base.volume_corners
  const project = (p) => [(p.x - p.y) * 0.82, p.z - (p.x + p.y) * 0.41]
  const panelPoints = g.side_panels.enabled ? ['left', 'right'].flatMap((name) => Object.values(g.side_panels[name])) : []
  const support = g.support.corners
  const all3d = [...Object.values(surface), ...Object.values(base), ...panelPoints, ...Object.values(support)]; const projected = all3d.map(project)
  const minV = Math.min(...projected.map(([, v]) => v)); const petU = Math.max(...projected.map(([u]) => u)) + (pet?.enabled ? 10 : 0)
  const framed = pet?.enabled ? [...projected, [petU + pet.length_cm, minV], [petU, minV + pet.height_cm]] : projected
  const f = frame(framed)
  const q = (p) => { const [u, v] = project(p); return `${f.x(u)},${f.y(v)}` }
  return <Projection title="Аксонометрия"><svg viewBox="0 0 700 410">
    <polygon points={`${q(base.bottom_a_left)} ${q(base.bottom_c_left)} ${q(base.bottom_c_right)} ${q(base.bottom_a_right)}`} fill={COLORS[ramp.color]} className="axon-base-bottom" />
    <polygon points={`${q(base.top_a_left)} ${q(base.top_c_left)} ${q(base.bottom_c_left)} ${q(base.bottom_a_left)}`} fill={COLORS[ramp.color]} className="axon-base-side" />
    <polygon points={`${q(base.top_c_left)} ${q(base.top_c_right)} ${q(base.bottom_c_right)} ${q(base.bottom_c_left)}`} fill={COLORS[ramp.color]} className="axon-base-end" />
    <polygon points={`${q(base.top_a_left)} ${q(base.top_c_left)} ${q(base.top_c_right)} ${q(base.top_a_right)}`} fill={COLORS[ramp.color]} stroke={COLORS[ramp.color]} className="projection-base axon" />
    <polygon points={`${q(support.foot_left_back)} ${q(support.hinge_left_back)} ${q(support.hinge_right_back)} ${q(support.foot_right_back)}`} fill={COLORS[ramp.color]} className="axon-support-panel support-back" />
    <polygon points={`${q(support.foot_left_front)} ${q(support.hinge_left_front)} ${q(support.hinge_right_front)} ${q(support.foot_right_front)}`} fill={COLORS[ramp.color]} className="axon-support-panel support-front" />
    <polygon points={`${q(support.foot_left_back)} ${q(support.foot_left_front)} ${q(support.hinge_left_front)} ${q(support.hinge_left_back)}`} fill={COLORS[ramp.color]} className="axon-support-panel support-side" />
    <polygon points={`${q(support.foot_right_back)} ${q(support.foot_right_front)} ${q(support.hinge_right_front)} ${q(support.hinge_right_back)}`} fill={COLORS[ramp.color]} className="axon-support-panel support-side" />
    <polygon points={`${q(surface.top_a_left)} ${q(surface.top_b_left)} ${q(surface.bottom_b_left)} ${q(surface.bottom_a_left)}`} fill={COLORS[ramp.color]} className="axon-surface-side" />
    <polygon points={`${q(surface.top_b_left)} ${q(surface.top_b_right)} ${q(surface.bottom_b_right)} ${q(surface.bottom_b_left)}`} fill={COLORS[ramp.color]} className="axon-surface-end" />
    <polygon points={`${q(surface.top_a_left)} ${q(surface.top_b_left)} ${q(surface.top_b_right)} ${q(surface.top_a_right)}`} fill={COLORS[ramp.color]} stroke={COLORS[ramp.color]} className="projection-surface axon-surface" />
    {g.steps.map((s) => <g key={s.start_distance_cm}>
      <polygon points={`${q(s.start_left)} ${q(s.end_left)} ${q(s.top_end_left)} ${q(s.top_start_left)}`} fill={COLORS[ramp.color]} className="axon-slat-side" />
      <polygon points={`${q(s.end_left)} ${q(s.end_right)} ${q(s.top_end_right)} ${q(s.top_end_left)}`} fill={COLORS[ramp.color]} className="axon-slat-end" />
      <polygon points={`${q(s.top_start_left)} ${q(s.top_end_left)} ${q(s.top_end_right)} ${q(s.top_start_right)}`} fill={COLORS[ramp.color]} className="projection-step-band axon-step" />
    </g>)}
    {g.side_panels.enabled && ['left', 'right'].map((name) => {
      const panel = g.side_panels[name]
      return <polygon key={name} points={`${q(panel.top_start)} ${q(panel.top_end)} ${q(panel.bottom_end)} ${q(panel.bottom_start)}`} fill={COLORS[ramp.color]} className="axon-side-panel" />
    })}
    <DogSilhouette pet={pet} view="side" x={f.x(petU)} groundY={f.y(minV)} heightPx={f.scale * (pet?.height_cm || 0)} />
    <text x="22" y="385">Стойка по центру ширины · рейки закреплены поверх листа</text>
  </svg></Projection>
}

function Projection({ title, children }) { return <figure className="diagram-card projection-card"><figcaption>{title}</figcaption>{children}</figure> }

const views = [
  ['side', 'Сбоку'], ['top', 'Сверху'], ['front', 'Спереди'], ['axon', 'Аксонометрия'], ['all', 'Все виды'],
]

export default function ProjectionViewer({ ramp, pet, view: controlledView, onViewChange, displayOptions = {}, containerRef }) {
  const [internalView, setInternalView] = useState('all')
  const view = controlledView ?? internalView
  const setView = (next) => { setInternalView(next); onViewChange?.(next) }
  if (ramp.product_state === 'folded') return <section ref={containerRef} className="projection-viewer"><div className="folded-preview"><strong>Сложенное состояние — предварительно</strong><p>Точная геометрия складывания и оси петель ещё не подтверждены. Технический чертёж не строится, чтобы не выдавать предварительную схему за производственный размер.</p></div></section>
  const content = { side: <RampDiagram ramp={ramp} pet={pet} />, top: <TopView ramp={ramp} pet={pet} />, front: <FrontView ramp={ramp} pet={pet} />, axon: <AxonometricView ramp={ramp} pet={pet} /> }
  const classes = ['projection-viewer', displayOptions.theme === 'dark' ? 'image-theme-dark' : '', displayOptions.showLabels === false ? 'hide-image-labels' : '', displayOptions.showDimensions === false ? 'hide-image-dimensions' : ''].filter(Boolean).join(' ')
  return <section ref={containerRef} className={classes} style={{ '--image-background': displayOptions.background || '#ffffff', '--image-scale': `${displayOptions.scale || 100}%` }}>
    <nav className="view-tabs" aria-label="Проекции изделия">{views.map(([id, label]) => <button key={id} className={view === id ? 'active' : ''} onClick={() => setView(id)}>{label}</button>)}</nav>
    {view === 'all' ? <div className="all-views">{Object.values(content)}</div> : content[view]}
  </section>
}

