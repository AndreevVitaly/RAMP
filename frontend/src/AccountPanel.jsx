import { useEffect, useState } from 'react'
import { downloadCurrentBriefPdf, downloadTechnicalBriefPdf, getAdminSettings, getSavedProjects, saveProject, sendTechnicalBrief, sendTechnicalBriefPdf, setCustomerPassword } from './api'
import { CUSTOMER_TOKEN_KEY } from './accessSession'

export default function AccountPanel({ customer: initialCustomer, configuration, result, busy, onLoadProject, onSwitchUser }) {
  const [customer, setCustomer] = useState(initialCustomer)
  const [message, setMessage] = useState('')
  const [comment, setComment] = useState('')
  const [channels, setChannels] = useState({ email: true, telegram: false, max: false })
  const [contacts, setContacts] = useState({})
  const [pdfBusy, setPdfBusy] = useState(false)
  const [downloadBusy, setDownloadBusy] = useState(false)
  const [pdfId, setPdfId] = useState(null)
  const [projects, setProjects] = useState([])
  const [projectName, setProjectName] = useState('')
  const [savingProject, setSavingProject] = useState(false)
  const [passwords, setPasswords] = useState({ current_password: '', new_password: '' })
  const [savingPassword, setSavingPassword] = useState(false)

  function handleAccountError(error) {
    if (error.status === 401 || error.status === 403) {
      onSwitchUser()
      return
    }
    setMessage(error.message)
  }

  useEffect(() => {
    getAdminSettings().then(setContacts).catch(() => {})
  }, [])

  useEffect(() => {
    if (!customer) return
    getSavedProjects(localStorage.getItem(CUSTOMER_TOKEN_KEY)).then(setProjects).catch(handleAccountError)
  }, [customer?.id])

  async function saveCurrentProject(event) {
    event.preventDefault(); setMessage(''); setSavingProject(true)
    try {
      const saved = await saveProject(localStorage.getItem(CUSTOMER_TOKEN_KEY), { name: projectName.trim(), configuration })
      setProjects((current) => [saved, ...current]); setProjectName('')
      setMessage(`Проект «${saved.name}» сохранён.`)
    } catch (error) { handleAccountError(error) }
    finally { setSavingProject(false) }
  }

  async function submitPassword(event) {
    event.preventDefault(); setMessage(''); setSavingPassword(true)
    const details = event.currentTarget.closest('details')
    try {
      const response = await setCustomerPassword(localStorage.getItem(CUSTOMER_TOKEN_KEY), passwords)
      setCustomer({ ...customer, has_password: true })
      setPasswords({ current_password: '', new_password: '' })
      setMessage(response.detail)
      details.open = false
    } catch (error) { handleAccountError(error) }
    finally { setSavingPassword(false) }
  }

  function chooseProject(project, event) {
    event.currentTarget.closest('details').open = false
    onLoadProject(project.configuration)
    setMessage(`Параметры проекта «${project.name}» загружены в конструктор.`)
  }

  async function submitBrief(event) {
    event.preventDefault(); setMessage('')
    try {
      const requested = Object.entries(channels).filter(([, enabled]) => enabled).map(([name]) => name)
      const response = await sendTechnicalBrief(localStorage.getItem(CUSTOMER_TOKEN_KEY), { message: comment, configuration, result, requested_channels: requested })
      const delivered = Object.entries(response.delivery_status).map(([key, value]) => `${key}: ${value === 'sent' ? 'отправлено' : value === 'not_configured' ? 'не настроено' : 'ошибка'}`).join(', ')
      setMessage(`Техническое задание №${response.id} сохранено. ${delivered}`); setComment('')
    } catch (error) { handleAccountError(error) }
  }

  async function submitPdf() {
    setMessage(''); setPdfBusy(true); setPdfId(null)
    try {
      const response = await sendTechnicalBriefPdf(localStorage.getItem(CUSTOMER_TOKEN_KEY), { message: comment, configuration })
      setPdfId(response.id)
      const label = (value) => value === 'sent' ? 'отправлено' : value === 'console_only' ? 'только локальная почтовая консоль' : 'ошибка отправки'
      setMessage(`PDF №${response.id} создан. Администратору: ${label(response.delivery_status.admin)}; клиенту: ${label(response.delivery_status.customer)}.`)
    } catch (error) { handleAccountError(error) }
    finally { setPdfBusy(false) }
  }

  async function downloadCurrentPdf() {
    setMessage(''); setDownloadBusy(true)
    try {
      await downloadCurrentBriefPdf(localStorage.getItem(CUSTOMER_TOKEN_KEY), { message: comment, configuration })
      setMessage('PDF сохранён на ваше устройство.')
    } catch (error) { handleAccountError(error) }
    finally { setDownloadBusy(false) }
  }

  return <section id="customer-account" className="panel account-panel">
    <div className="section-heading"><div><p className="eyebrow">Личный кабинет</p><h2>{customer ? `Здравствуйте, ${customer.name}` : 'Вход и регистрация'}</h2></div>{customer && <button type="button" className="link-button" onClick={onSwitchUser}>Выйти</button>}</div>
    {!customer && <div className="account-form compact"><p>Войдите по email, чтобы увидеть свои проекты и отправить техническое задание.</p><button className="primary-button" type="button" onClick={onSwitchUser}>Войти в личный кабинет</button></div>}
    {customer && <details className="project-dropdown"><summary>{customer.has_password ? 'Изменить пароль' : 'Задать пароль для входа'}</summary>
      <form className="access-form" onSubmit={submitPassword}>
        {customer.has_password && <label className="field"><span>Текущий пароль</span><input required type="password" autoComplete="current-password" value={passwords.current_password} onChange={(event) => setPasswords({ ...passwords, current_password: event.target.value })} /></label>}
        <label className="field"><span>Новый пароль (не менее 10 символов)</span><input required type="password" minLength="10" maxLength="128" autoComplete="new-password" value={passwords.new_password} onChange={(event) => setPasswords({ ...passwords, new_password: event.target.value })} /></label>
        <button className="primary-button" type="submit" disabled={savingPassword}>Сохранить пароль</button>
      </form>
    </details>}
    {customer && <section className="saved-projects" aria-labelledby="saved-projects-title">
      <div><h3 id="saved-projects-title">Мои проекты</h3><p>Сохраните размеры изделия, чтобы вернуться к ним позже.</p></div>
      <form className="project-save-form" onSubmit={saveCurrentProject}>
        <label className="field"><span>Название проекта (необязательно)</span><input maxLength={120} placeholder="Например, пандус для дивана" value={projectName} onChange={(event) => setProjectName(event.target.value)} /></label>
        <button className="primary-button" type="submit" disabled={!result || busy || savingProject}>{savingProject ? 'Сохраняем…' : 'Сохранить проект'}</button>
      </form>
      {projects.length ? <details className="project-dropdown"><summary>Открыть сохранённый проект ({projects.length})</summary><div className="project-dropdown-list">{projects.map((project) => <button key={project.id} type="button" onClick={(event) => chooseProject(project, event)}><strong>{project.name}</strong><small>{new Date(project.created_at).toLocaleDateString('ru-RU')}</small></button>)}</div></details> : <p>Пока нет сохранённых проектов.</p>}
    </section>}
    {customer && result && <form className="brief-form" onSubmit={submitBrief}>
      <div className="account-summary"><span>{customer.email}</span>{customer.phone && <span>{customer.phone}</span>}</div>
      <label className="field"><span>Комментарий к техническому заданию</span><textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Уточнения по размерам, доставке или конструкции" /></label>
      <fieldset className="channel-picker"><legend>Куда отправить</legend>
        <label><input type="checkbox" checked={channels.email} onChange={(e) => setChannels({ ...channels, email: e.target.checked })} /> Email {contacts.email && `(${contacts.email})`}</label>
        <label><input type="checkbox" checked={channels.telegram} onChange={(e) => setChannels({ ...channels, telegram: e.target.checked })} /> Telegram {contacts.telegram && `(${contacts.telegram})`}</label>
        <label><input type="checkbox" checked={channels.max} onChange={(e) => setChannels({ ...channels, max: e.target.checked })} /> MAX {contacts.max_contact && `(${contacts.max_contact})`}</label>
      </fieldset>
      <button className="primary-button" type="submit">Отправить техническое задание</button>
      <button className="secondary-button" type="button" disabled={downloadBusy} onClick={downloadCurrentPdf}>{downloadBusy ? 'Формируем PDF…' : 'Скачать PDF на устройство'}</button>
      <button className="secondary-button" type="button" disabled={pdfBusy} onClick={submitPdf}>{pdfBusy ? 'Формируем PDF…' : 'Сформировать PDF и отправить на обе почты'}</button>
      {pdfId && <button className="link-button" type="button" onClick={() => downloadTechnicalBriefPdf(localStorage.getItem(CUSTOMER_TOKEN_KEY), pdfId).catch(handleAccountError)}>Скачать PDF №{pdfId}</button>}
    </form>}
    {message && <div className="account-message" role="status">{message}</div>}
  </section>
}
