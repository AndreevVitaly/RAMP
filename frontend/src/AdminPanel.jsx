import { useEffect, useState } from 'react'
import { getAdminBriefs, getAdminProjects, getAdminSettings, saveAdminSettings } from './api'

export default function AdminPanel({ onClose, onSwitchUser, onOpenConfiguration }) {
  const adminToken = sessionStorage.getItem('ramp_admin_token') || ''
  const [settings, setSettings] = useState({ email: '', phone: '', telegram: '', max_contact: '', preferred_channel: 'email' })
  const [briefs, setBriefs] = useState([])
  const [projects, setProjects] = useState([])
  const [loadingEntries, setLoadingEntries] = useState(true)
  const [message, setMessage] = useState('')

  useEffect(() => {
    getAdminSettings().then(setSettings).catch(() => {})
    if (adminToken) Promise.all([getAdminBriefs(adminToken), getAdminProjects(adminToken)])
      .then(([loadedBriefs, loadedProjects]) => { setBriefs(loadedBriefs); setProjects(loadedProjects) })
      .catch((error) => setMessage(error.message))
      .finally(() => setLoadingEntries(false))
    else { setMessage('Войдите как администратор, чтобы увидеть проекты клиентов.'); setLoadingEntries(false) }
  }, [])

  async function save(event) {
    event.preventDefault(); setMessage('')
    try {
      const saved = await saveAdminSettings(adminToken, settings); setSettings(saved)
      setMessage('Контакты сохранены.')
    } catch (error) { setMessage(error.message) }
  }

  async function load() {
    setLoadingEntries(true)
    try {
      const [loadedBriefs, loadedProjects] = await Promise.all([getAdminBriefs(adminToken), getAdminProjects(adminToken)])
      setBriefs(loadedBriefs); setProjects(loadedProjects); setMessage('Списки обновлены.')
    } catch (error) { setMessage(error.message) }
    finally { setLoadingEntries(false) }
  }

  return <main><header><div className="brand">RAMP</div><div><p className="eyebrow">Рабочее пространство</p><h1>Кабинет администратора</h1><p>Контакты для клиентов и входящие технические задания.</p></div><div className="header-actions"><button type="button" className="secondary-button" onClick={onClose}>Вернуться к конструктору</button><button type="button" className="secondary-button" onClick={onSwitchUser}>Сменить пользователя</button></div></header>
    <div className="admin-grid">
      <form className="panel admin-settings" onSubmit={save}><h2>Контакты и доставка</h2>
        <div className="admin-authenticated">Вы вошли как администратор</div>
        <label className="field"><span>Email</span><input type="email" value={settings.email} onChange={(e) => setSettings({ ...settings, email: e.target.value })} /></label>
        <label className="field"><span>Телефон</span><input type="tel" value={settings.phone} onChange={(e) => setSettings({ ...settings, phone: e.target.value })} /></label>
        <label className="field"><span>Telegram</span><input placeholder="@username" value={settings.telegram} onChange={(e) => setSettings({ ...settings, telegram: e.target.value })} /></label>
        <label className="field"><span>MAX</span><input placeholder="Ссылка или идентификатор" value={settings.max_contact} onChange={(e) => setSettings({ ...settings, max_contact: e.target.value })} /></label>
        <label className="field"><span>Основной канал</span><select value={settings.preferred_channel} onChange={(e) => setSettings({ ...settings, preferred_channel: e.target.value })}><option value="email">Email</option><option value="telegram">Telegram</option><option value="max">MAX</option></select></label>
        <button className="primary-button" type="submit">Сохранить контакты</button>{message && <div className="account-message">{message}</div>}
      </form>
      <div className="admin-orders">
        <section className="panel admin-briefs"><div className="section-heading"><div><h2>Сохранённые проекты клиентов</h2><p>Параметры, которые клиенты сохранили в личном кабинете.</p></div><button type="button" className="secondary-button" onClick={load} disabled={loadingEntries}>Обновить</button></div>
          {loadingEntries ? <p>Загружаем проекты…</p> : !projects.length ? <p>Сохранённых проектов пока нет.</p> : projects.map((project) => <button key={project.id} className="client-project-card" type="button" onClick={() => onOpenConfiguration({ kind: 'project', id: project.id, name: project.name, customer: project.customer, configuration: project.configuration })}><span className="client-project-card-top"><strong>{project.name}</strong><small>Сохранённый проект</small></span><span>{project.customer.name} · {project.customer.email}</span><span>{project.configuration.height_cm} × {project.configuration.ramp_length_cm} × {project.configuration.width_cm} см · {new Date(project.updated_at).toLocaleString('ru-RU')}</span><em>Открыть в конструкторе →</em></button>)}
        </section>
        <section className="panel admin-briefs"><div className="section-heading"><h2>Отправленные технические задания</h2></div>
          {loadingEntries ? <p>Загружаем задания…</p> : !briefs.length ? <p>Клиенты пока не отправили технических заданий. Сохранённые проекты показаны выше.</p> : briefs.map((brief) => <article key={brief.id} className="brief-card"><div><strong>№{brief.id} · {brief.customer.name}</strong><time>{new Date(brief.created_at).toLocaleString('ru-RU')}</time></div><p>{[brief.customer.phone, brief.customer.email].filter(Boolean).join(' · ')}</p><p>{brief.message || 'Без комментария'}</p><small>{brief.configuration.height_cm} × {brief.configuration.ramp_length_cm} × {brief.configuration.width_cm} см · {brief.requested_channels.join(', ')}</small><button type="button" className="link-button" onClick={() => onOpenConfiguration({ kind: 'brief', id: brief.id, name: `Техническое задание №${brief.id}`, customer: brief.customer, configuration: brief.configuration })}>Открыть в конструкторе →</button></article>)}
        </section>
      </div>
    </div>
  </main>
}
