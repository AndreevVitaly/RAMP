import { useEffect, useState } from 'react'
import { getAdminBriefs, getAdminSettings, saveAdminSettings } from './api'

export default function AdminPanel({ onClose }) {
  const [key, setKey] = useState('')
  const [settings, setSettings] = useState({ email: '', phone: '', telegram: '', max_contact: '', preferred_channel: 'email' })
  const [briefs, setBriefs] = useState([])
  const [message, setMessage] = useState('')

  useEffect(() => { getAdminSettings().then(setSettings).catch(() => {}) }, [])

  async function save(event) {
    event.preventDefault(); setMessage('')
    try {
      const saved = await saveAdminSettings(key, settings); setSettings(saved)
      setBriefs(await getAdminBriefs(key)); setMessage('Контакты сохранены.')
    } catch (error) { setMessage(error.message) }
  }

  async function load() {
    try { setBriefs(await getAdminBriefs(key)); setMessage('Заявки обновлены.') } catch (error) { setMessage(error.message) }
  }

  return <main><header><div className="brand">RAMP</div><div><p className="eyebrow">Рабочее пространство</p><h1>Кабинет администратора</h1><p>Контакты для клиентов и входящие технические задания.</p></div><button type="button" className="secondary-button header-action" onClick={onClose}>Вернуться к конструктору</button></header>
    <div className="admin-grid">
      <form className="panel admin-settings" onSubmit={save}><h2>Контакты и доставка</h2>
        <label className="field"><span>Ключ администратора</span><input type="password" required value={key} onChange={(e) => setKey(e.target.value)} /></label>
        <label className="field"><span>Email</span><input type="email" value={settings.email} onChange={(e) => setSettings({ ...settings, email: e.target.value })} /></label>
        <label className="field"><span>Телефон</span><input type="tel" value={settings.phone} onChange={(e) => setSettings({ ...settings, phone: e.target.value })} /></label>
        <label className="field"><span>Telegram</span><input placeholder="@username" value={settings.telegram} onChange={(e) => setSettings({ ...settings, telegram: e.target.value })} /></label>
        <label className="field"><span>MAX</span><input placeholder="Ссылка или идентификатор" value={settings.max_contact} onChange={(e) => setSettings({ ...settings, max_contact: e.target.value })} /></label>
        <label className="field"><span>Основной канал</span><select value={settings.preferred_channel} onChange={(e) => setSettings({ ...settings, preferred_channel: e.target.value })}><option value="email">Email</option><option value="telegram">Telegram</option><option value="max">MAX</option></select></label>
        <button className="primary-button" type="submit">Сохранить и войти</button>{message && <div className="account-message">{message}</div>}
      </form>
      <section className="panel admin-briefs"><div className="section-heading"><h2>Технические задания</h2><button type="button" className="secondary-button" onClick={load}>Обновить</button></div>
        {!briefs.length ? <p>После входа здесь появятся заявки клиентов.</p> : briefs.map((brief) => <article key={brief.id} className="brief-card"><div><strong>№{brief.id} · {brief.customer.name}</strong><time>{new Date(brief.created_at).toLocaleString('ru-RU')}</time></div><p>{brief.customer.phone} · {brief.customer.email}</p><p>{brief.message || 'Без комментария'}</p><small>{brief.configuration.height_cm} × {brief.configuration.ramp_length_cm} × {brief.configuration.width_cm} см · {brief.requested_channels.join(', ')}</small></article>)}
      </section>
    </div>
  </main>
}
