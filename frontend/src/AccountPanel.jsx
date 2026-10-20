import { useEffect, useState } from 'react'
import { downloadTechnicalBriefPdf, getAccount, getAdminSettings, requestEmailCode, sendTechnicalBrief, sendTechnicalBriefPdf, verifyEmailCode } from './api'
import EmailCodeDialog from './EmailCodeDialog'

const TOKEN_KEY = 'ramp_customer_token'

export default function AccountPanel({ configuration, result }) {
  const [customer, setCustomer] = useState(null)
  const [registration, setRegistration] = useState({ name: '', email: '', phone: '' })
  const [code, setCode] = useState('')
  const [awaitingCode, setAwaitingCode] = useState(false)
  const [devCode, setDevCode] = useState('')
  const [message, setMessage] = useState('')
  const [comment, setComment] = useState('')
  const [channels, setChannels] = useState({ email: true, telegram: false, max: false })
  const [contacts, setContacts] = useState({})
  const [pdfBusy, setPdfBusy] = useState(false)
  const [pdfId, setPdfId] = useState(null)

  useEffect(() => {
    getAdminSettings().then(setContacts).catch(() => {})
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) getAccount(token).then(setCustomer).catch(() => localStorage.removeItem(TOKEN_KEY))
  }, [])

  async function requestCode(event) {
    event.preventDefault(); setMessage('')
    try {
      const response = await requestEmailCode(registration)
      setAwaitingCode(true); setDevCode(response.dev_code || ''); setCode(''); setMessage('')
    } catch (error) { setMessage(error.message) }
  }

  async function verify(event) {
    event.preventDefault(); setMessage('')
    try {
      const response = await verifyEmailCode(registration.email, code)
      localStorage.setItem(TOKEN_KEY, response.token); setCustomer(response.customer); setAwaitingCode(false); setMessage('Электронная почта подтверждена.')
    } catch (error) { setMessage(error.message) }
  }

  async function submitBrief(event) {
    event.preventDefault(); setMessage('')
    try {
      const requested = Object.entries(channels).filter(([, enabled]) => enabled).map(([name]) => name)
      const response = await sendTechnicalBrief(localStorage.getItem(TOKEN_KEY), { message: comment, configuration, result, requested_channels: requested })
      const delivered = Object.entries(response.delivery_status).map(([key, value]) => `${key}: ${value === 'sent' ? 'отправлено' : value === 'not_configured' ? 'не настроено' : 'ошибка'}`).join(', ')
      setMessage(`Техническое задание №${response.id} сохранено. ${delivered}`); setComment('')
    } catch (error) { setMessage(error.message) }
  }

  async function submitPdf() {
    setMessage(''); setPdfBusy(true); setPdfId(null)
    try {
      const response = await sendTechnicalBriefPdf(localStorage.getItem(TOKEN_KEY), { message: comment, configuration })
      setPdfId(response.id)
      const label = (value) => value === 'sent' ? 'отправлено' : value === 'console_only' ? 'только локальная почтовая консоль' : 'ошибка отправки'
      setMessage(`PDF №${response.id} создан. Администратору: ${label(response.delivery_status.admin)}; клиенту: ${label(response.delivery_status.customer)}.`)
    } catch (error) { setMessage(error.message) }
    finally { setPdfBusy(false) }
  }

  function logout() { localStorage.removeItem(TOKEN_KEY); setCustomer(null); setAwaitingCode(false); setCode('') }

  return <section id="customer-account" className="panel account-panel">
    <div className="section-heading"><div><p className="eyebrow">Личный кабинет</p><h2>{customer ? `Здравствуйте, ${customer.name}` : 'Вход и регистрация'}</h2></div>{customer && <button type="button" className="link-button" onClick={logout}>Выйти</button>}</div>
    {!customer && <form className="account-form" onSubmit={requestCode}>
      <label className="field"><span>Имя</span><input required value={registration.name} onChange={(e) => setRegistration({ ...registration, name: e.target.value })} /></label>
      <label className="field"><span>Электронная почта</span><input required type="email" value={registration.email} onChange={(e) => setRegistration({ ...registration, email: e.target.value })} /></label>
      <label className="field"><span>Телефон (необязательно)</span><input type="tel" placeholder="+7 900 000-00-00" value={registration.phone} onChange={(e) => setRegistration({ ...registration, phone: e.target.value })} /></label>
      <button className="primary-button" type="submit">Получить код на email</button>
    </form>}
    {customer && <form className="brief-form" onSubmit={submitBrief}>
      <div className="account-summary"><span>{customer.email}</span>{customer.phone && <span>{customer.phone}</span>}</div>
      <label className="field"><span>Комментарий к техническому заданию</span><textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Уточнения по размерам, доставке или конструкции" /></label>
      <fieldset className="channel-picker"><legend>Куда отправить</legend>
        <label><input type="checkbox" checked={channels.email} onChange={(e) => setChannels({ ...channels, email: e.target.checked })} /> Email {contacts.email && `(${contacts.email})`}</label>
        <label><input type="checkbox" checked={channels.telegram} onChange={(e) => setChannels({ ...channels, telegram: e.target.checked })} /> Telegram {contacts.telegram && `(${contacts.telegram})`}</label>
        <label><input type="checkbox" checked={channels.max} onChange={(e) => setChannels({ ...channels, max: e.target.checked })} /> MAX {contacts.max_contact && `(${contacts.max_contact})`}</label>
      </fieldset>
      <button className="primary-button" type="submit">Отправить техническое задание</button>
      <button className="secondary-button" type="button" disabled={pdfBusy} onClick={submitPdf}>{pdfBusy ? 'Формируем PDF…' : 'Сформировать PDF и отправить на обе почты'}</button>
      {pdfId && <button className="link-button" type="button" onClick={() => downloadTechnicalBriefPdf(localStorage.getItem(TOKEN_KEY), pdfId).catch((error) => setMessage(error.message))}>Скачать PDF №{pdfId}</button>}
    </form>}
    {message && !awaitingCode && <div className="account-message" role="status">{message}</div>}
    {awaitingCode && <EmailCodeDialog email={registration.email} code={code} devCode={devCode} message={message} onChange={setCode} onSubmit={verify} onClose={() => { setAwaitingCode(false); setMessage('') }} />}
  </section>
}
