import { useEffect, useState } from 'react'
import { getAccount, loginAdmin, requestEmailCode, verifyEmailCode } from './api'
import EmailCodeDialog from './EmailCodeDialog'

const TOKEN_KEY = 'ramp_customer_token'
const GUEST_KEY = 'ramp_guest_access'
const ADMIN_TOKEN_KEY = 'ramp_admin_token'

export default function AccessGate({ children }) {
  const [access, setAccess] = useState('checking')
  const [step, setStep] = useState('choice')
  const [registration, setRegistration] = useState({ name: '', email: '', phone: '' })
  const [code, setCode] = useState('')
  const [devCode, setDevCode] = useState('')
  const [codeDialogOpen, setCodeDialogOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [admin, setAdmin] = useState({ username: 'admin', password: '' })

  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      getAccount(token).then(() => setAccess('allowed')).catch(() => { localStorage.removeItem(TOKEN_KEY); setAccess('gate') })
    } else if (sessionStorage.getItem(GUEST_KEY)) setAccess('allowed')
    else setAccess('gate')
  }, [])

  async function requestCode(event) {
    event.preventDefault(); setMessage('')
    try {
      const response = await requestEmailCode(registration)
      setDevCode(response.dev_code || ''); setCode(''); setCodeDialogOpen(true); setMessage('')
    } catch (error) { setMessage(error.message) }
  }

  async function verify(event) {
    event.preventDefault(); setMessage('')
    try {
      const response = await verifyEmailCode(registration.email, code)
      localStorage.setItem(TOKEN_KEY, response.token); sessionStorage.removeItem(GUEST_KEY); setAccess('allowed')
    } catch (error) { setMessage(error.message) }
  }

  function continueAsGuest() { sessionStorage.setItem(GUEST_KEY, 'true'); setAccess('allowed') }

  async function adminLogin(event) {
    event.preventDefault(); setMessage('')
    try {
      const response = await loginAdmin(admin.username, admin.password)
      sessionStorage.setItem(ADMIN_TOKEN_KEY, response.token); sessionStorage.setItem(GUEST_KEY, 'true'); setAccess('allowed')
    } catch (error) { setMessage(error.message) }
  }

  if (access === 'checking') return <div className="access-loading">Загружаем RAMP…</div>
  if (access === 'allowed') return children

  return <main className="access-page"><section className="access-card">
    <div className="brand">RAMP</div>
    {step === 'choice' && <>
      <p className="eyebrow">Добро пожаловать</p><h1>Пандус, рассчитанный для вашего питомца</h1>
      <p className="access-lead">Зарегистрируйтесь, чтобы отправлять заказы и технические задания, или откройте сайт в режиме просмотра.</p>
      <div className="access-actions"><button className="primary-button" type="button" onClick={() => setStep('register')}>Зарегистрироваться</button><button className="secondary-button" type="button" onClick={continueAsGuest}>Посмотреть без регистрации</button><button className="admin-entry-button" type="button" onClick={() => setStep('admin')}>Я администратор</button></div>
      <small>В режиме просмотра можно пользоваться конструктором, но отправка заказа будет недоступна.</small>
    </>}
    {step === 'register' && <form className="access-form" onSubmit={requestCode}>
      <p className="eyebrow">Регистрация</p><h2>Контактные данные</h2>
      <label className="field"><span>Имя</span><input required autoComplete="name" value={registration.name} onChange={(e) => setRegistration({ ...registration, name: e.target.value })} /></label>
      <label className="field"><span>Электронная почта</span><input required type="email" autoComplete="email" value={registration.email} onChange={(e) => setRegistration({ ...registration, email: e.target.value })} /></label>
      <label className="field"><span>Телефон для связи (необязательно)</span><input type="tel" autoComplete="tel" placeholder="+7 900 000-00-00" value={registration.phone} onChange={(e) => setRegistration({ ...registration, phone: e.target.value })} /></label>
      <button className="primary-button" type="submit">Получить код на email</button><button className="link-button" type="button" onClick={() => setStep('choice')}>Назад</button>
    </form>}
    {step === 'admin' && <form className="access-form" onSubmit={adminLogin}>
      <p className="eyebrow">Вход администратора</p><h2>Управление RAMP</h2>
      <label className="field"><span>Логин</span><input required autoComplete="username" value={admin.username} onChange={(e) => setAdmin({ ...admin, username: e.target.value })} /></label>
      <label className="field"><span>Пароль</span><input required type="password" autoComplete="current-password" value={admin.password} onChange={(e) => setAdmin({ ...admin, password: e.target.value })} /></label>
      <button className="primary-button" type="submit">Войти на главный экран</button><button className="link-button" type="button" onClick={() => setStep('choice')}>Назад</button>
    </form>}
    {message && !codeDialogOpen && <div className="account-message" role="status">{message}</div>}
  </section>{codeDialogOpen && <EmailCodeDialog email={registration.email} code={code} devCode={devCode} message={message} onChange={setCode} onSubmit={verify} onClose={() => { setCodeDialogOpen(false); setMessage('') }} />}</main>
}
