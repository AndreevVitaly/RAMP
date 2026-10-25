import { useEffect, useState } from 'react'
import { getAccount, getAdminBriefs, loginAdmin, requestEmailCode, requestLoginCode, verifyEmailCode } from './api'
import { ADMIN_TOKEN_KEY, clearAccessStorage, CUSTOMER_TOKEN_KEY, GUEST_ACCESS_KEY } from './accessSession'
import EmailCodeDialog from './EmailCodeDialog'

export default function AccessGate({ children }) {
  const [access, setAccess] = useState('checking')
  const [step, setStep] = useState('choice')
  const [registration, setRegistration] = useState({ name: '', email: '', phone: '' })
  const [loginEmail, setLoginEmail] = useState('')
  const [codeEmail, setCodeEmail] = useState('')
  const [code, setCode] = useState('')
  const [devCode, setDevCode] = useState('')
  const [codeDialogOpen, setCodeDialogOpen] = useState(false)
  const [message, setMessage] = useState('')
  const [admin, setAdmin] = useState({ username: 'admin', password: '' })

  useEffect(() => {
    const adminToken = sessionStorage.getItem(ADMIN_TOKEN_KEY)
    if (adminToken) {
      getAdminBriefs(adminToken).then(() => setAccess('allowed')).catch(() => {
        sessionStorage.removeItem(ADMIN_TOKEN_KEY); setAccess('gate')
      })
      return
    }
    const token = localStorage.getItem(CUSTOMER_TOKEN_KEY)
    if (token) {
      getAccount(token).then(() => setAccess('allowed')).catch(() => { localStorage.removeItem(CUSTOMER_TOKEN_KEY); setAccess('gate') })
    } else if (sessionStorage.getItem(GUEST_ACCESS_KEY)) setAccess('allowed')
    else setAccess('gate')
  }, [])

  async function requestRegistrationCode(event) {
    event.preventDefault(); setMessage('')
    try {
      const response = await requestEmailCode(registration)
      setCodeEmail(registration.email.trim()); setDevCode(response.dev_code || ''); setCode(''); setCodeDialogOpen(true); setMessage('')
    } catch (error) { setMessage(error.message) }
  }

  async function requestExistingLoginCode(event) {
    event.preventDefault(); setMessage('')
    try {
      const email = loginEmail.trim()
      const response = await requestLoginCode(email)
      setCodeEmail(email); setDevCode(response.dev_code || ''); setCode(''); setCodeDialogOpen(true); setMessage('')
    } catch (error) { setMessage(error.message) }
  }

  async function verify(event) {
    event.preventDefault(); setMessage('')
    try {
      const response = await verifyEmailCode(codeEmail, code)
      localStorage.setItem(CUSTOMER_TOKEN_KEY, response.token); sessionStorage.removeItem(GUEST_ACCESS_KEY); sessionStorage.removeItem(ADMIN_TOKEN_KEY); setAccess('allowed')
    } catch (error) { setMessage(error.message) }
  }

  function continueAsGuest() { localStorage.removeItem(CUSTOMER_TOKEN_KEY); sessionStorage.removeItem(ADMIN_TOKEN_KEY); sessionStorage.setItem(GUEST_ACCESS_KEY, 'true'); setAccess('allowed') }

  async function adminLogin(event) {
    event.preventDefault(); setMessage('')
    try {
      const response = await loginAdmin(admin.username, admin.password)
      sessionStorage.setItem(ADMIN_TOKEN_KEY, response.token); sessionStorage.removeItem(GUEST_ACCESS_KEY); localStorage.removeItem(CUSTOMER_TOKEN_KEY); setAccess('allowed')
    } catch (error) { setMessage(error.message) }
  }

  function switchUser() {
    clearAccessStorage()
    setStep('choice')
    setRegistration({ name: '', email: '', phone: '' })
    setLoginEmail(''); setCodeEmail('')
    setAdmin({ username: 'admin', password: '' })
    setCode(''); setDevCode(''); setCodeDialogOpen(false); setMessage('')
    setAccess('gate')
    window.scrollTo(0, 0)
  }

  if (access === 'checking') return <div className="access-loading">Загружаем RAMP…</div>
  if (access === 'allowed') return children(switchUser)

  return <main className="access-page"><section className="access-card">
    <div className="brand">RAMP</div>
    {step === 'choice' && <>
      <p className="eyebrow">Добро пожаловать</p><h1>Пандус, рассчитанный для вашего питомца</h1>
      <p className="access-lead">Войдите по коду из email, чтобы открыть свой кабинет и сохранённые проекты, или зарегистрируйтесь впервые.</p>
      <div className="access-actions"><button className="primary-button" type="button" onClick={() => setStep('login')}>Войти</button><button className="secondary-button" type="button" onClick={() => setStep('register')}>Зарегистрироваться</button><button className="secondary-button guest-entry-button" type="button" onClick={continueAsGuest}>Посмотреть без регистрации</button><button className="admin-entry-button" type="button" onClick={() => setStep('admin')}>Я администратор</button></div>
      <small>В режиме просмотра можно пользоваться конструктором, но отправка заказа будет недоступна.</small>
    </>}
    {step === 'login' && <form className="access-form" onSubmit={requestExistingLoginCode}>
      <p className="eyebrow">Личный кабинет</p><h2>Вход для зарегистрированных</h2>
      <p>Укажите email, который использовали при регистрации. Мы пришлём одноразовый код.</p>
      <label className="field"><span>Электронная почта</span><input required type="email" autoComplete="email" value={loginEmail} onChange={(e) => setLoginEmail(e.target.value)} /></label>
      <button className="primary-button" type="submit">Получить код для входа</button><button className="link-button" type="button" onClick={() => { setMessage(''); setStep('register') }}>Нет аккаунта? Зарегистрироваться</button><button className="link-button" type="button" onClick={() => { setMessage(''); setStep('choice') }}>Назад</button>
    </form>}
    {step === 'register' && <form className="access-form" onSubmit={requestRegistrationCode}>
      <p className="eyebrow">Первый вход</p><h2>Регистрация</h2>
      <label className="field"><span>Имя</span><input required autoComplete="name" value={registration.name} onChange={(e) => setRegistration({ ...registration, name: e.target.value })} /></label>
      <label className="field"><span>Электронная почта</span><input required type="email" autoComplete="email" value={registration.email} onChange={(e) => setRegistration({ ...registration, email: e.target.value })} /></label>
      <label className="field"><span>Телефон для связи (необязательно)</span><input type="tel" autoComplete="tel" placeholder="+7 900 000-00-00" value={registration.phone} onChange={(e) => setRegistration({ ...registration, phone: e.target.value })} /></label>
      <button className="primary-button" type="submit">Получить код на email</button><button className="link-button" type="button" onClick={() => { setMessage(''); setStep('login') }}>Уже зарегистрированы? Войти</button><button className="link-button" type="button" onClick={() => { setMessage(''); setStep('choice') }}>Назад</button>
    </form>}
    {step === 'admin' && <form className="access-form" onSubmit={adminLogin}>
      <p className="eyebrow">Вход администратора</p><h2>Управление RAMP</h2>
      <label className="field"><span>Логин</span><input required autoComplete="username" value={admin.username} onChange={(e) => setAdmin({ ...admin, username: e.target.value })} /></label>
      <label className="field"><span>Пароль</span><input required type="password" autoComplete="current-password" value={admin.password} onChange={(e) => setAdmin({ ...admin, password: e.target.value })} /></label>
      <button className="primary-button" type="submit">Войти на главный экран</button><button className="link-button" type="button" onClick={() => setStep('choice')}>Назад</button>
    </form>}
    {message && !codeDialogOpen && <div className="account-message" role="status">{message}</div>}
  </section>{codeDialogOpen && <EmailCodeDialog email={codeEmail} code={code} devCode={devCode} message={message} login={step === 'login'} onChange={setCode} onSubmit={verify} onClose={() => { setCodeDialogOpen(false); setMessage('') }} />}</main>
}
