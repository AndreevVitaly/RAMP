import { useEffect, useState } from 'react'
import { calculateRamp } from './api'
import RampDiagram from './RampDiagram'

const initialForm = { height_cm: 50, ramp_length_cm: 100, width_cm: 40, color: 'dark_gray', side_rails: false }

function NumberField({ label, name, value, onChange, hint }) {
  return <label className="field"><span>{label}</span><div className="number-input"><input type="number" name={name} value={value} min="0" step="1" onChange={onChange} /><em>см</em></div>{hint && <small>{hint}</small>}</label>
}

export default function App() {
  const [form, setForm] = useState(initialForm)
  const [lengthEdited, setLengthEdited] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  function update(event) {
    const { name, value, checked, type } = event.target
    const nextValue = type === 'checkbox' ? checked : type === 'number' ? Number(value) : value
    setForm((current) => {
      const next = { ...current, [name]: nextValue }
      if (name === 'height_cm' && !lengthEdited) next.ramp_length_cm = nextValue * 2
      return next
    })
    if (name === 'ramp_length_cm') setLengthEdited(true)
  }

  function useRecommendation() {
    setForm((current) => ({ ...current, ramp_length_cm: current.height_cm * 2 }))
    setLengthEdited(false)
  }

  useEffect(() => {
    const controller = new AbortController()
    const timeout = setTimeout(async () => {
      setLoading(true)
      setError('')
      try {
        const payload = { ...form }
        if (!lengthEdited) delete payload.ramp_length_cm
        setResult(await calculateRamp(payload, controller.signal))
      } catch (err) {
        if (err.name !== 'AbortError') { setError(err.message); setResult(null) }
      } finally { setLoading(false) }
    }, 250)
    return () => { clearTimeout(timeout); controller.abort() }
  }, [form, lengthEdited])

  return <main>
    <header><div className="brand">RAMP</div><div><p className="eyebrow">Конструктор пандусов для собак</p><h1>Рассчитайте удобный подъём</h1><p>Задайте размеры — мы рассчитаем геометрию и расположение поперечных реек.</p></div></header>
    <div className="workspace">
      <section className="panel form-panel">
        <h2>Параметры</h2>
        <NumberField label="Высота подъёма" name="height_cm" value={form.height_cm} onChange={update} />
        <NumberField label="Длина поверхности" name="ramp_length_cm" value={form.ramp_length_cm} onChange={update} hint={`Рекомендация: ${form.height_cm * 2} см`} />
        {lengthEdited && <button className="link-button" type="button" onClick={useRecommendation}>Вернуть рекомендуемую длину</button>}
        <NumberField label="Ширина" name="width_cm" value={form.width_cm} onChange={update} hint="Стандартная ширина — 40 см" />
        <label className="field"><span>Цвет покрытия</span><select name="color" value={form.color} onChange={update}><option value="dark_gray">Тёмно-серый</option><option value="light_gray">Светло-серый</option><option value="black">Чёрный</option><option value="beige">Бежевый</option></select></label>
        <label className="toggle"><input type="checkbox" name="side_rails" checked={form.side_rails} onChange={update} /><span>Добавить боковые бортики</span></label>
      </section>
      <section className="results">
        {loading && <div className="notice">Пересчитываем…</div>}
        {error && <div className="notice error">{error}</div>}
        {result && <>
          <RampDiagram ramp={result} />
          <div className="panel metrics"><h2>Результат расчёта</h2><dl>
            <div><dt>Рекомендуемая длина</dt><dd>{result.recommended_length_cm} см</dd></div>
            <div><dt>Выбранная длина</dt><dd>{result.ramp_length_cm} см</dd></div>
            <div><dt>Высота / ширина</dt><dd>{result.height_cm} / {result.width_cm} см</dd></div>
            <div><dt>Угол наклона</dt><dd>{result.angle_deg}°</dd></div>
            <div><dt>Количество реек</dt><dd>{result.step_count}</dd></div>
            <div><dt>Длина основания</dt><dd>{result.geometry.base_length_cm} см</dd></div>
            <div><dt>Длина стойки</dt><dd>{result.geometry.support_length_cm} см</dd></div>
            <div><dt>Угол стойки</dt><dd>{result.geometry.support_base_angle_deg}°</dd></div>
            <div><dt>Механика стойки</dt><dd>Складная, 2 петли</dd></div>
            <div><dt>Рабочее состояние</dt><dd>{result.geometry.support.state === 'deployed' ? 'Разложена' : 'Сложена'}</dd></div>
            <div className="wide"><dt>Положения реек</dt><dd>{result.step_positions_cm.join(', ')} см</dd></div>
          </dl></div>
        </>}
      </section>
    </div>
  </main>
}

