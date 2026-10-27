import { useEffect, useState } from 'react'
import { calculateRamp, downloadCurrentBriefPdf } from './api'
import ProjectionViewer from './ProjectionViewer'
import ImageStudio from './ImageStudio'
import { PET_BREEDS, petPreset } from './pets'
import AccountPanel from './AccountPanel'
import AdminPanel from './AdminPanel'
import { ADMIN_TOKEN_KEY, CUSTOMER_TOKEN_KEY } from './accessSession'

const initialForm = { height_cm: 50, ramp_length_cm: 100, width_cm: 40, support_panel_width_cm: 20, color: 'dark_gray', has_slats: true, side_rails: false, product_state: 'deployed' }

function NumberField({ label, name, value, onChange, hint, min = 0 }) {
  return <label className="field"><span>{label}</span><div className="number-input"><input type="number" name={name} value={value} min={min} step="1" onChange={onChange} /><em>см</em></div>{hint && <small>{hint}</small>}</label>
}

const rubles = (value) => new Intl.NumberFormat('ru-RU').format(value) + ' ₽'

export default function App({ onSwitchUser }) {
  const [form, setForm] = useState(initialForm)
  const [lengthEdited, setLengthEdited] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [pet, setPet] = useState({ enabled: false, ...petPreset('dachshund') })
  const [screen, setScreen] = useState('calculator')
  const [adminPreview, setAdminPreview] = useState(null)
  const [pdfBusy, setPdfBusy] = useState(false)
  const [pdfMessage, setPdfMessage] = useState('')

  async function downloadAdminPdf() {
    setPdfMessage('')
    setPdfBusy(true)
    try {
      await downloadCurrentBriefPdf(sessionStorage.getItem(ADMIN_TOKEN_KEY), {
        configuration: form,
        ...(adminPreview?.customer?.id ? { customer_id: adminPreview.customer.id } : {}),
      })
      setPdfMessage('PDF сохранён на устройство.')
    } catch (downloadError) {
      setPdfMessage(downloadError.message)
    } finally {
      setPdfBusy(false)
    }
  }

  function updatePet(event) {
    const { name, value, checked, type } = event.target
    if (name === 'breed') {
      setPet((current) => ({ ...current, ...petPreset(value) }))
      return
    }
    setPet((current) => ({ ...current, [name]: type === 'checkbox' ? checked : type === 'number' ? Number(value) : value }))
  }

  function update(event) {
    const { name, value, checked, type } = event.target
    const nextValue = type === 'checkbox' ? checked : type === 'number' ? Number(value) : value
    setLoading(true)
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

  function loadProject(configuration) {
    const { pet: savedPet, ...product } = configuration
    const breed = savedPet?.breed && PET_BREEDS[savedPet.breed] ? savedPet.breed : 'dachshund'
    setForm({ ...initialForm, ...product })
    setPet({ enabled: Boolean(savedPet?.enabled), ...petPreset(breed) })
    setLengthEdited(true)
    setLoading(true)
    setResult(null)
    document.querySelector('.form-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  function openClientConfiguration(item) {
    loadProject(item.configuration)
    setAdminPreview(item)
    setScreen('calculator')
    window.scrollTo(0, 0)
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

  if (screen === 'admin') return <AdminPanel onClose={() => { setAdminPreview(null); setScreen('calculator') }} onSwitchUser={onSwitchUser} onOpenConfiguration={openClientConfiguration} />

  return <main>
    <header><div className="brand">RAMP</div><div><p className="eyebrow">Конструктор пандусов для собак</p><h1>Рассчитайте удобный подъём</h1><p>Задайте размеры — мы рассчитаем геометрию и расположение поперечных реек.</p></div><div className="header-actions">{sessionStorage.getItem(ADMIN_TOKEN_KEY) && <button type="button" className="secondary-button" onClick={() => setScreen('admin')}>Кабинет администратора</button>}{!sessionStorage.getItem(ADMIN_TOKEN_KEY) && localStorage.getItem(CUSTOMER_TOKEN_KEY) && <><button type="button" className="primary-button" onClick={() => document.getElementById('saved-projects-title')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>Перейти к сохранению</button><button type="button" className="secondary-button" onClick={() => document.getElementById('customer-account')?.scrollIntoView({ behavior: 'smooth' })}>Личный кабинет</button></>}<button type="button" className="secondary-button" onClick={onSwitchUser}>Сменить пользователя</button></div></header>
    {adminPreview && <section className="admin-preview-banner"><div><strong>Просмотр: {adminPreview.name}</strong><p>{adminPreview.customer.name} · {adminPreview.customer.email} · {adminPreview.kind === 'project' ? 'сохранённый проект' : 'отправленное техническое задание'}. Изменения в этом конструкторе не меняют запись клиента.</p></div><button type="button" className="secondary-button" onClick={() => { setAdminPreview(null); setScreen('admin') }}>Вернуться к списку</button></section>}
    <div className="workspace">
      <section className="panel form-panel">
        <h2>Параметры</h2>
        <NumberField label="Высота подъёма" name="height_cm" value={form.height_cm} onChange={update} />
        <NumberField label="Длина поверхности" name="ramp_length_cm" value={form.ramp_length_cm} onChange={update} min={60} hint={`Рекомендация: ${form.height_cm * 2} см · минимум 60 см`} />
        {lengthEdited && <button className="link-button" type="button" onClick={useRecommendation}>Вернуть рекомендуемую длину</button>}
        <NumberField label="Ширина" name="width_cm" value={form.width_cm} onChange={update} hint="Стандартная ширина — 40 см" />
        <NumberField label="Ширина опорной стойки" name="support_panel_width_cm" value={form.support_panel_width_cm} onChange={update} hint="Стандартная ширина — 20 см" />
        <label className="field"><span>Цвет покрытия</span><select name="color" value={form.color} onChange={update}><option value="dark_gray">Тёмно-серый</option><option value="light_gray">Светло-серый</option><option value="black">Чёрный</option><option value="beige">Бежевый</option></select></label>
        <label className="toggle"><input type="checkbox" name="has_slats" checked={form.has_slats} onChange={update} /><span>Добавить поперечные рейки</span></label>
        <label className="toggle"><input type="checkbox" name="side_rails" checked={form.side_rails} onChange={update} /><span>Добавить боковые бортики</span></label>
        <fieldset className="pet-controls">
          <legend>Питомец для масштаба</legend>
          <label className="toggle"><input type="checkbox" name="enabled" checked={pet.enabled} onChange={updatePet} /><span>Показывать питомца</span></label>
          {pet.enabled && <>
            <label className="field"><span>Порода</span><select name="breed" value={pet.breed} onChange={updatePet}>{Object.entries(PET_BREEDS).map(([id, breed]) => <option key={id} value={id}>{breed.label}</option>)}</select></label>
            <div className="pet-breed-info"><strong>{PET_BREEDS[pet.breed].height_cm} см</strong><span>средняя высота в холке</span></div>
            <small className="pet-hint">Размер автоматически задан по породе и используется для масштаба на изображении.</small>
          </>}
        </fieldset>
        <section className="price-card" aria-live="polite"><h2>Стоимость изделия</h2>{!loading && result?.price ? <>
          <div><span>Пандус {result.price.length_cm} см</span><strong>{rubles(result.price.base_price_rub)}</strong></div>
          <div><span>Боковые бортики</span><strong>{result.price.side_rails_price_rub ? rubles(result.price.side_rails_price_rub) : 'Не выбраны'}</strong></div>
          <div><span>Поперечные рейки</span><strong>{result.has_slats ? 'Включены, бесплатно' : 'Не выбраны'}</strong></div>
          <div className="price-total"><span>Итого</span><strong>{rubles(result.price.total_price_rub)}</strong></div>
        </> : <p>{loading ? 'Обновляем стоимость…' : 'Укажите допустимые размеры.'}</p>}</section>
      </section>
      <section className="results">
        {loading && <div className="notice">Пересчитываем…</div>}
        {error && <div className="notice error">{error}</div>}
        {result && <>
          <ProjectionViewer ramp={result} pet={pet} />
          {sessionStorage.getItem(ADMIN_TOKEN_KEY) && <div className="panel"><button className="secondary-button" type="button" disabled={pdfBusy} onClick={downloadAdminPdf}>{pdfBusy ? 'Формируем PDF…' : 'Скачать PDF на устройство'}</button>{pdfMessage && <p role="status">{pdfMessage}</p>}</div>}
          <div className="panel metrics"><h2>Результат расчёта</h2><dl>
            <div><dt>Рекомендуемая длина</dt><dd>{result.recommended_length_cm} см</dd></div>
            <div><dt>Выбранная длина</dt><dd>{result.ramp_length_cm} см</dd></div>
            <div><dt>Высота / ширина</dt><dd>{result.height_cm} / {result.width_cm} см</dd></div>
            <div><dt>Угол наклона</dt><dd>{result.angle_deg}°</dd></div>
            <div><dt>Поперечные рейки</dt><dd>{result.has_slats ? 'Есть' : 'Нет'}</dd></div>
            {result.has_slats && <div><dt>Количество реек</dt><dd>{result.step_count}</dd></div>}
            {result.has_slats && <div><dt>Рейка: высота × ширина × длина</dt><dd>{result.step_height_cm} × {result.step_width_cm} × {result.width_cm} см</dd></div>}
            <div><dt>Длина основания</dt><dd>{Math.round(result.geometry.base_length_cm)} см</dd></div>
            <div><dt>Длина стойки</dt><dd>{result.geometry.support_length_cm} см</dd></div>
            <div><dt>Ширина стойки</dt><dd>{result.geometry_3d.support.panel_width_cm} см</dd></div>
            <div><dt>Угол стойки</dt><dd>{result.geometry.support_base_angle_deg}°</dd></div>
            <div><dt>Положение шарнира</dt><dd>{result.geometry.support.hinge_position_ratio * 100}% / {result.geometry.support.hinge_distance_cm} см</dd></div>
            <div><dt>Зазор от опоры до C</dt><dd>{result.geometry.support_foot_to_base_end_cm} см</dd></div>
            <div><dt>Механика стойки</dt><dd>Складная, 2 петли</dd></div>
            {result.geometry_3d.side_panels.enabled ? <>
              <div><dt>Боковые панели</dt><dd>2 шт.</dd></div>
              <div><dt>Длина каждой</dt><dd>{result.geometry_3d.side_panels.length_cm} см</dd></div>
              <div><dt>Высота каждой</dt><dd>{result.geometry_3d.side_panels.height_cm} см</dd></div>
              <div><dt>Площадь двух панелей с одной стороны</dt><dd>{result.geometry_3d.side_panels.area_total_one_side_cm2} см²</dd></div>
            </> : <div><dt>Боковые панели</dt><dd>Нет</dd></div>}
            {result.has_slats && <div className="wide"><dt>Положения реек</dt><dd>{result.step_positions_cm.join(', ')} см</dd></div>}
          </dl></div>
          <ImageStudio ramp={result} configuration={form} pet={pet} />
        </>}
        {!adminPreview && <AccountPanel configuration={{ ...form, pet }} result={result} busy={loading} onLoadProject={loadProject} onSwitchUser={onSwitchUser} />}
      </section>
    </div>
  </main>
}
