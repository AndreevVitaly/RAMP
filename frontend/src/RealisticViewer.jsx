import { useState } from 'react'
import { COLORS } from './materials'

function shade(hex, amount) {
  const value = parseInt(hex.slice(1), 16)
  const channel = (shift) => Math.max(0, Math.min(255, ((value >> shift) & 255) + amount)).toString(16).padStart(2, '0')
  return `#${channel(16)}${channel(8)}${channel(0)}`
}

function frame(points, width = 760, height = 500, margin = 58) {
  const xs = points.map(([x]) => x); const ys = points.map(([, y]) => y)
  const minX = Math.min(...xs); const maxX = Math.max(...xs); const minY = Math.min(...ys); const maxY = Math.max(...ys)
  const scale = Math.min((width - margin * 2) / Math.max(maxX - minX, 1), (height - margin * 2) / Math.max(maxY - minY, 1))
  const ox = (width - (maxX - minX) * scale) / 2; const oy = (height - (maxY - minY) * scale) / 2
  return { x: (x) => ox + (x - minX) * scale, y: (y) => height - oy - (y - minY) * scale }
}

function MaterialDefs({ color }) {
  return <defs>
    <linearGradient id="carpetLight" x1="0" y1="0" x2="1" y2="1"><stop stopColor={shade(color, 35)} /><stop offset=".55" stopColor={color} /><stop offset="1" stopColor={shade(color, -28)} /></linearGradient>
    <linearGradient id="carpetSide" x1="0" y1="0" x2="0" y2="1"><stop stopColor={shade(color, -4)} /><stop offset="1" stopColor={shade(color, -42)} /></linearGradient>
    <filter id="softShadow" x="-30%" y="-30%" width="160%" height="180%"><feDropShadow dx="7" dy="10" stdDeviation="8" floodOpacity=".28" /></filter>
    <filter id="carpetTexture" x="-10%" y="-10%" width="120%" height="120%"><feTurbulence type="fractalNoise" baseFrequency=".48" numOctaves="2" seed="8" result="noise" /><feColorMatrix in="noise" values=".22 0 0 0 .58  0 .22 0 0 .58  0 0 .22 0 .58  0 0 0 .18 0" result="grain" /><feBlend in="SourceGraphic" in2="grain" mode="multiply" /></filter>
    <filter id="slatRelief" x="-20%" y="-80%" width="140%" height="260%"><feDropShadow dx="2" dy="3" stdDeviation="3" floodColor="#000" floodOpacity=".35" /></filter>
  </defs>
}

function AxonView({ ramp }) {
  const g = ramp.geometry_3d; const color = COLORS[ramp.color]; const surface = g.ramp_surface.volume_corners; const base = g.base.volume_corners; const support = g.support.corners
  const project = (p) => [(p.x - p.y) * .86, p.z - (p.x + p.y) * .32]
  const all = [...Object.values(surface), ...Object.values(base), ...Object.values(support), ...(g.side_panels.enabled ? ['left', 'right'].flatMap((name) => Object.values(g.side_panels[name])) : [])]
  const f = frame(all.map(project)); const q = (p) => { const [x, y] = project(p); return `${f.x(x)},${f.y(y)}` }
  return <svg viewBox="0 0 760 500" role="img" aria-label="Реалистичная аксонометрия пандуса"><MaterialDefs color={color} />
    <ellipse cx="390" cy="424" rx="270" ry="35" fill="#182018" opacity=".13" filter="url(#softShadow)" />
    <g filter="url(#softShadow)">
      <polygon points={`${q(base.bottom_a_left)} ${q(base.bottom_c_left)} ${q(base.bottom_c_right)} ${q(base.bottom_a_right)}`} fill={shade(color, -45)} />
      <polygon points={`${q(base.top_a_left)} ${q(base.top_c_left)} ${q(base.bottom_c_left)} ${q(base.bottom_a_left)}`} fill="url(#carpetSide)" />
      <polygon points={`${q(base.top_a_right)} ${q(base.top_c_right)} ${q(base.bottom_c_right)} ${q(base.bottom_a_right)}`} fill={shade(color, -34)} />
      <polygon points={`${q(base.top_a_left)} ${q(base.top_c_left)} ${q(base.top_c_right)} ${q(base.top_a_right)}`} fill="url(#carpetLight)" filter="url(#carpetTexture)" />
      <polygon points={`${q(support.foot_left_back)} ${q(support.hinge_left_back)} ${q(support.hinge_right_back)} ${q(support.foot_right_back)}`} fill={shade(color, -38)} />
      <polygon points={`${q(support.foot_left_front)} ${q(support.hinge_left_front)} ${q(support.hinge_right_front)} ${q(support.foot_right_front)}`} fill="url(#carpetLight)" filter="url(#carpetTexture)" />
      <polygon points={`${q(support.foot_left_back)} ${q(support.foot_left_front)} ${q(support.hinge_left_front)} ${q(support.hinge_left_back)}`} fill="url(#carpetSide)" />
      <polygon points={`${q(surface.top_a_left)} ${q(surface.top_b_left)} ${q(surface.bottom_b_left)} ${q(surface.bottom_a_left)}`} fill="url(#carpetSide)" />
      <polygon points={`${q(surface.top_b_left)} ${q(surface.top_b_right)} ${q(surface.bottom_b_right)} ${q(surface.bottom_b_left)}`} fill={shade(color, -28)} />
      <polygon points={`${q(surface.top_a_left)} ${q(surface.top_b_left)} ${q(surface.top_b_right)} ${q(surface.top_a_right)}`} fill="url(#carpetLight)" filter="url(#carpetTexture)" />
      {g.steps.map((step) => <polygon key={step.start_distance_cm} points={`${q(step.start_left)} ${q(step.end_left)} ${q(step.end_right)} ${q(step.start_right)}`} fill={shade(color, 13)} opacity=".82" filter="url(#slatRelief)" />)}
      {g.side_panels.enabled && ['left', 'right'].map((name) => { const p = g.side_panels[name]; return <polygon key={name} points={`${q(p.bottom_start)} ${q(p.bottom_end)} ${q(p.top_end)} ${q(p.top_start)}`} fill="url(#carpetSide)" filter="url(#carpetTexture)" /> })}
    </g>
  </svg>
}

function SideView({ ramp }) {
  const g = ramp.geometry_3d; const color = COLORS[ramp.color]; const s = g.ramp_surface.volume_corners; const support = g.support.corners
  const points = Object.values(s).map((p) => [p.x, p.z]).concat(Object.values(g.base.volume_corners).map((p) => [p.x, p.z])); const f = frame(points)
  const q = (p) => `${f.x(p.x)},${f.y(p.z)}`
  return <svg viewBox="0 0 760 500"><MaterialDefs color={color} /><ellipse cx="390" cy="431" rx="280" ry="22" fill="#172018" opacity=".14" />
    <polygon points={`${q(g.base.volume_corners.top_a_left)} ${q(g.base.volume_corners.top_c_left)} ${q(g.base.volume_corners.bottom_c_left)} ${q(g.base.volume_corners.bottom_a_left)}`} fill="url(#carpetSide)" filter="url(#softShadow)" />
    <polygon points={`${q(support.foot_left_front)} ${q(support.hinge_left_front)} ${q(support.hinge_left_back)} ${q(support.foot_left_back)}`} fill="url(#carpetLight)" filter="url(#carpetTexture)" />
    <polygon points={`${q(s.top_a_left)} ${q(s.top_b_left)} ${q(s.bottom_b_left)} ${q(s.bottom_a_left)}`} fill="url(#carpetLight)" filter="url(#softShadow)" />
    {!g.side_panels.enabled && g.steps.map((step) => <line key={step.start_distance_cm} x1={f.x(step.start_left.x)} y1={f.y(step.start_left.z)} x2={f.x(step.end_left.x)} y2={f.y(step.end_left.z)} stroke={shade(color, 18)} strokeWidth="8" filter="url(#slatRelief)" />)}
    {g.side_panels.enabled && <polygon points={`${q(g.side_panels.left.bottom_start)} ${q(g.side_panels.left.bottom_end)} ${q(g.side_panels.left.top_end)} ${q(g.side_panels.left.top_start)}`} fill="url(#carpetSide)" filter="url(#carpetTexture)" />}
  </svg>
}

function TopView({ ramp }) {
  const g = ramp.geometry_3d; const color = COLORS[ramp.color]; const { horizontal_run_cm: run, width_cm: width } = g.dimensions; const f = frame([[0, 0], [run, width]])
  return <svg viewBox="0 0 760 500"><MaterialDefs color={color} /><rect x={f.x(0)} y={f.y(width)} width={f.x(run) - f.x(0)} height={f.y(0) - f.y(width)} rx="4" fill="url(#carpetLight)" filter="url(#carpetTexture)" />{g.steps.map((step) => <polygon key={step.start_distance_cm} points={`${f.x(step.start_left.x)},${f.y(0)} ${f.x(step.end_left.x)},${f.y(0)} ${f.x(step.end_right.x)},${f.y(width)} ${f.x(step.start_right.x)},${f.y(width)}`} fill={shade(color, 16)} opacity=".78" filter="url(#slatRelief)" />)}</svg>
}

function FrontView({ ramp }) {
  const g = ramp.geometry_3d; const color = COLORS[ramp.color]; const support = g.support; const f = frame([[0, 0], [g.dimensions.width_cm, g.dimensions.height_cm + 6]])
  return <svg viewBox="0 0 760 500"><MaterialDefs color={color} /><rect x={f.x(support.y_min_cm)} y={f.y(g.support.axis.hinge.z)} width={f.x(support.y_max_cm) - f.x(support.y_min_cm)} height={f.y(0) - f.y(g.support.axis.hinge.z)} fill="url(#carpetLight)" filter="url(#carpetTexture)" /><line x1={f.x(0)} y1={f.y(g.dimensions.height_cm)} x2={f.x(g.dimensions.width_cm)} y2={f.y(g.dimensions.height_cm)} stroke={color} strokeWidth="10" />{g.side_panels.enabled && [0, g.dimensions.width_cm].map((y) => <line key={y} x1={f.x(y)} y1={f.y(g.dimensions.height_cm)} x2={f.x(y)} y2={f.y(g.dimensions.height_cm + 5)} stroke={color} strokeWidth="7" />)}</svg>
}

const VIEWS = { axon: ['Аксонометрия', AxonView], side: ['Сбоку', SideView], top: ['Сверху', TopView], front: ['Спереди', FrontView] }

export default function RealisticViewer({ ramp, view, onViewChange, containerRef, displayOptions = {} }) {
  const [internal, setInternal] = useState('axon'); const active = view || internal; const Component = VIEWS[active][1]
  const select = (next) => { setInternal(next); onViewChange?.(next) }
  if (ramp.product_state === 'folded') return <div className="folded-preview"><strong>Сложенное состояние — предварительно</strong><p>Точная кинематика петель и положение стойки ещё не подтверждены. RAMP сохраняет выбранное состояние, но не показывает недостоверную геометрию или толщину сложенного изделия.</p></div>
  return <div ref={containerRef} className="realistic-viewer" style={{ '--image-scale': `${displayOptions.scale || 100}%` }}><div className="realistic-main" style={{ background: displayOptions.showBackground === false ? 'transparent' : displayOptions.background }}><Component ramp={ramp} /></div><div className="realistic-thumbnails">{Object.entries(VIEWS).map(([id, [label, View]]) => <button type="button" key={id} className={id === active ? 'active' : ''} onClick={() => select(id)}><View ramp={ramp} /><span>{label}</span></button>)}</div></div>
}
