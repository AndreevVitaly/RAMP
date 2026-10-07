import { useState } from 'react'
import RampDiagram from './RampDiagram'

const COLORS = { dark_gray: '#4a4f55', light_gray: '#aab0b5', black: '#202226', beige: '#c7ad85' }

function frame(points, width = 700, height = 410, margin = 55) {
  const xs = points.map((p) => p[0]); const ys = points.map((p) => p[1])
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys)
  const scale = Math.min((width - margin * 2) / Math.max(maxX - minX, 1), (height - margin * 2) / Math.max(maxY - minY, 1))
  return { width, height, x: (v) => margin + (v - minX) * scale, y: (v) => height - margin - (v - minY) * scale }
}

function centeredFrame(points, width = 700, height = 410, margin = 24) {
  const xs = points.map((p) => p[0]); const ys = points.map((p) => p[1])
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys)
  const contentWidth = Math.max(maxX - minX, 1); const contentHeight = Math.max(maxY - minY, 1)
  const scale = Math.min((width - margin * 2) / contentWidth, (height - margin * 2) / contentHeight)
  const offsetX = (width - contentWidth * scale) / 2
  const offsetY = (height - contentHeight * scale) / 2
  return { width, height, x: (v) => offsetX + (v - minX) * scale, y: (v) => height - offsetY - (v - minY) * scale }
}

function TopView({ ramp }) {
  const g = ramp.geometry_3d; const { horizontal_run_cm: run, width_cm: w } = g.dimensions
  const f = centeredFrame([[0, 0], [run, w]])
  return <figure className="diagram-card projection-card top-product-view"><svg viewBox="0 0 700 410" role="img" aria-label="Пандус, вид сверху">
    <polygon points={`${f.x(0)},${f.y(0)} ${f.x(run)},${f.y(0)} ${f.x(run)},${f.y(w)} ${f.x(0)},${f.y(w)}`} fill={COLORS[ramp.color]} stroke={COLORS[ramp.color]} className="projection-surface product-surface" />
    {g.steps.map((s) => <polygon key={s.start_distance_cm} points={`${f.x(s.start_left.x)},${f.y(s.start_left.y)} ${f.x(s.end_left.x)},${f.y(s.end_left.y)} ${f.x(s.end_right.x)},${f.y(s.end_right.y)} ${f.x(s.start_right.x)},${f.y(s.start_right.y)}`} fill={COLORS[ramp.color]} className="projection-step-band" />)}
    {g.side_rails.enabled && <>
      <line x1={f.x(g.side_rails.left.top_start.x)} y1={f.y(g.side_rails.left.top_start.y)} x2={f.x(g.side_rails.left.top_end.x)} y2={f.y(g.side_rails.left.top_end.y)} stroke={COLORS[ramp.color]} className="top-side-rail" />
      <line x1={f.x(g.side_rails.right.top_start.x)} y1={f.y(g.side_rails.right.top_start.y)} x2={f.x(g.side_rails.right.top_end.x)} y2={f.y(g.side_rails.right.top_end.y)} stroke={COLORS[ramp.color]} className="top-side-rail" />
    </>}
  </svg></figure>
}

function FrontView({ ramp }) {
  const g = ramp.geometry_3d; const { height_cm: h, width_cm: w } = g.dimensions; const f = frame([[0, 0], [w, h]])
  return <Projection title="Вид спереди · YZ"><svg viewBox="0 0 700 410">
    <rect x={f.x(0)} y={f.y(h)} width={f.x(w) - f.x(0)} height={f.y(0) - f.y(h)} fill={`${COLORS[ramp.color]}18`} stroke={COLORS[ramp.color]} className="projection-surface" />
    <line x1={f.x(0)} y1={f.y(0)} x2={f.x(w)} y2={f.y(0)} className="base-line" />
    {g.steps.map((s) => <rect key={s.start_distance_cm} x={f.x(0)} y={f.y(s.end_left.z)} width={f.x(w) - f.x(0)} height={f.y(s.start_left.z) - f.y(s.end_left.z)} fill={COLORS[ramp.color]} className="projection-step-band front" />)}
    {g.side_rails.enabled && <>
      <line x1={f.x(g.side_rails.left.bottom_start.y)} y1={f.y(g.side_rails.left.bottom_start.z)} x2={f.x(g.side_rails.left.top_start.y)} y2={f.y(g.side_rails.left.top_start.z)} stroke={COLORS[ramp.color]} className="front-side-rail" />
      <line x1={f.x(g.side_rails.right.bottom_start.y)} y1={f.y(g.side_rails.right.bottom_start.z)} x2={f.x(g.side_rails.right.top_start.y)} y2={f.y(g.side_rails.right.top_start.z)} stroke={COLORS[ramp.color]} className="front-side-rail" />
    </>}
    <text x={f.x(w / 2)} y={f.y(0) + 28} textAnchor="middle">ширина {w} см</text>
    <text x={f.x(w) + 12} y={f.y(h / 2)}>высота {h} см</text>
  </svg></Projection>
}

function AxonometricView({ ramp }) {
  const g = ramp.geometry_3d; const surface = g.ramp_surface.corners; const base = g.base.corners
  const project = (p) => [(p.x - p.y) * 0.82, p.z - (p.x + p.y) * 0.34]
  const all3d = [...Object.values(surface), ...Object.values(base)]; const projected = all3d.map(project); const f = frame(projected)
  const q = (p) => { const [u, v] = project(p); return `${f.x(u)},${f.y(v)}` }
  const line = (a, b, cls, key) => <line key={key} x1={f.x(project(a)[0])} y1={f.y(project(a)[1])} x2={f.x(project(b)[0])} y2={f.y(project(b)[1])} className={cls} />
  return <Projection title="Аксонометрия"><svg viewBox="0 0 700 410">
    <polygon points={`${q(base.a_left)} ${q(base.c_left)} ${q(base.c_right)} ${q(base.a_right)}`} className="projection-base axon" />
    <polygon points={`${q(surface.a_left)} ${q(surface.b_left)} ${q(surface.b_right)} ${q(surface.a_right)}`} fill={`${COLORS[ramp.color]}44`} stroke={COLORS[ramp.color]} className="projection-surface" />
    {g.steps.map((s) => <polygon key={s.start_distance_cm} points={`${q(s.start_left)} ${q(s.end_left)} ${q(s.end_right)} ${q(s.start_right)}`} fill={COLORS[ramp.color]} className="projection-step-band axon-step" />)}
    {g.side_rails.enabled && <>
      <polygon points={`${q(g.side_rails.left.bottom_start)} ${q(g.side_rails.left.bottom_end)} ${q(g.side_rails.left.top_end)} ${q(g.side_rails.left.top_start)}`} fill={COLORS[ramp.color]} className="axon-side-rail" />
      <polygon points={`${q(g.side_rails.right.bottom_start)} ${q(g.side_rails.right.bottom_end)} ${q(g.side_rails.right.top_end)} ${q(g.side_rails.right.top_start)}`} fill={COLORS[ramp.color]} className="axon-side-rail" />
    </>}
    {line(g.support.axis.foot, g.support.axis.hinge, 'support-line', 'support')}
    {line(g.hinge_axis.left, g.hinge_axis.right, 'projection-hinge', 'hinge')}
    {line(g.support_stop.left, g.support_stop.right, 'projection-stop', 'stop')}
    <text x="22" y="385">Одна модель XYZ · стойка показана по центральной оси</text>
  </svg></Projection>
}

function Projection({ title, children }) { return <figure className="diagram-card projection-card"><figcaption>{title}</figcaption>{children}</figure> }

const views = [
  ['side', 'Сбоку'], ['top', 'Сверху'], ['front', 'Спереди'], ['axon', 'Аксонометрия'], ['all', 'Все виды'],
]

export default function ProjectionViewer({ ramp }) {
  const [view, setView] = useState('all')
  const content = { side: <RampDiagram ramp={ramp} />, top: <TopView ramp={ramp} />, front: <FrontView ramp={ramp} />, axon: <AxonometricView ramp={ramp} /> }
  return <section className="projection-viewer">
    <nav className="view-tabs" aria-label="Проекции изделия">{views.map(([id, label]) => <button key={id} className={view === id ? 'active' : ''} onClick={() => setView(id)}>{label}</button>)}</nav>
    {view === 'all' ? <div className="all-views">{Object.values(content)}</div> : content[view]}
  </section>
}

