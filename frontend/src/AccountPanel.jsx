import { useEffect, useState } from 'react'
import { getAccount, getAdminSettings, requestPhoneCode, sendTechnicalBrief, verifyPhoneCode } from './api'

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

  useEffect(() => {
    getAdminSettings().then(setContacts).catch(() => {})
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) getAccount(token).then(setCustomer).catch(() => localStorage.removeItem(TOKEN_KEY))
  }, [])

  async function requestCode(event) {
    event.preventDefault(); setMessage('')
    try {
      const response = await requestPhoneCode(registration)
      setAwaitingCode(true); setDevCode(response.dev_code || '')
      setMessage(response.sms_configured ? 'Код отправлен по SMS.' : 'Тестовый код создан.')
    } catch (error) { setMessage(error.message) }
  }

  async function verify(event) {
    event.preventDefault(); setMessage('')
    try {
      const response = await verifyPhoneCode(registration.phone, code)
      localStorage.setItem(TOKEN_KEY, response.token); setCustomer(response.customer); setMessage('Телефон подтверждён.')
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

  function logout() { localStorage.removeItem(TOKEN_KEY); setCustomer(null); setAwaitingCode(false); setCode('') }

  return <section id="customer-account" className="panel account-panel">
    <div className="section-heading"><div><p className="eyebrow">Личный кабинет</p><h2>{customer ? `Здравствуйте, ${customer.name}` : 'Вход и регистрация'}</h2></div>{customer && <button type="button" className="link-button" onClick={logout}>Выйти</button>}</div>
    {!customer && !awaitingCode && <form className="account-form" onSubmit={requestCode}>
      <label className="field"><span>Имя</span><input required value={registration.name} onChange={(e) => setRegistration({ ...registration, name: e.target.value })} /></label>
      <label className="field"><span>Электронная почта</span><input required type="email" value={registration.email} onChange={(e) => setRegistration({ ...registration, email: e.target.value })} /></label>
      <label className="field"><span>Телефон</span><input required type="tel" placeholder="+7 900 000-00-00" value={registration.phone} onChange={(e) => setRegistration({ ...registration, phone: e.target.value })} /></label>
      <button className="primary-button" type="submit">Получить код по SMS</button>
    </form>}
    {!customer && awaitingCode && <form className="account-form compact" onSubmit={verify}>
      <p>Введите шестизначный код, отправленный на {registration.phone}.</p>
      {devCode && <div className="dev-code">Код для локальной разработки: <strong>{devCode}</strong></div>}
      <label className="field"><span>Код подтверждения</span><input required inputMode="numeric" maxLength="6" value={code} onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))} /></label>
      <button className="primary-button" type="submit">Подтвердить телефон</button>
      <button className="link-button" type="button" onClick={() => setAwaitingCode(false)}>Изменить данные</button>
    </form>}
    {customer && <form className="brief-form" onSubmit={submitBrief}>
      <div className="account-summary"><span>{customer.email}</span><span>{customer.phone}</span></div>
      <label className="field"><span>Комментарий к техническому заданию</span><textarea value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Уточнения по размерам, доставке или конструкции" /></label>
      <fieldset className="channel-picker"><legend>Куда отправить</legend>
        <label><input type="checkbox" checked={channels.email} onChange={(e) => setChannels({ ...channels, email: e.target.checked })} /> Email {contacts.email && `(${contacts.email})`}</label>
        <label><input type="checkbox" checked={channels.telegram} onChange={(e) => setChannels({ ...channels, telegram: e.target.checked })} /> Telegram {contacts.telegram && `(${contacts.telegram})`}</label>
        <label><input type="checkbox" checked={channels.max} onChange={(e) => setChannels({ ...channels, max: e.target.checked })} /> MAX {contacts.max_contact && `(${contacts.max_contact})`}</label>
      </fieldset>
      <button className="primary-button" type="submit">Отправить техническое задание</button>
    </form>}
    {message && <div className="account-message" role="status">{message}</div>}
  </section>
}
