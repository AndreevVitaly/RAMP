import { useEffect, useState } from 'react'
import { getAccount, getAdminBriefs, loginAdmin, loginCustomer, registerCustomer } from './api'
import { ADMIN_TOKEN_KEY, clearAccessStorage, CUSTOMER_TOKEN_KEY, GUEST_ACCESS_KEY } from './accessSession'

export default function AccessGate({ children }) {
  const [access, setAccess] = useState('checking')
  const [step, setStep] = useState('login')
  const [registration, setRegistration] = useState({ name: '', email: '', password: '' })
  const [login, setLogin] = useState({ email: '', password: '' })
  const [admin, setAdmin] = useState({ username: 'admin', password: '' })
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

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
      getAccount(token).then(() => setAccess('allowed')).catch(() => {
        localStorage.removeItem(CUSTOMER_TOKEN_KEY); setAccess('gate')
      })
    } else if (sessionStorage.getItem(GUEST_ACCESS_KEY)) setAccess('allowed')
    else setAccess('gate')
  }, [])

  function enterCustomer(response) {
    localStorage.setItem(CUSTOMER_TOKEN_KEY, response.token)
    sessionStorage.removeItem(GUEST_ACCESS_KEY)
    sessionStorage.removeItem(ADMIN_TOKEN_KEY)
    setAccess('allowed')
  }

  async function submitLogin(event) {
    event.preventDefault(); setMessage(''); setBusy(true)
    try { enterCustomer(await loginCustomer(login.email.trim(), login.password)) }
    catch (error) { setMessage(error.message) }
    finally { setBusy(false) }
  }

  async function submitRegistration(event) {
    event.preventDefault(); setMessage(''); setBusy(true)
    try { enterCustomer(await registerCustomer({ ...registration, name: registration.name.trim(), email: registration.email.trim() })) }
    catch (error) { setMessage(error.message) }
    finally { setBusy(false) }
  }

  async function submitAdmin(event) {
    event.preventDefault(); setMessage(''); setBusy(true)
    try {
      const response = await loginAdmin(admin.username, admin.password)
      sessionStorage.setItem(ADMIN_TOKEN_KEY, response.token)
      sessionStorage.removeItem(GUEST_ACCESS_KEY)
      localStorage.removeItem(CUSTOMER_TOKEN_KEY)
      setAccess('allowed')
    } catch (error) { setMessage(error.message) }
    finally { setBusy(false) }
  }

  function continueAsGuest() {
    clearAccessStorage()
    sessionStorage.setItem(GUEST_ACCESS_KEY, 'true')
    setAccess('allowed')
  }

  function switchUser() {
    clearAccessStorage()
    setStep('login')
    setRegistration({ name: '', email: '', password: '' })
    setLogin({ email: '', password: '' })
    setAdmin({ username: 'admin', password: '' })
    setMessage('')
    setAccess('gate')
    window.scrollTo(0, 0)
  }

  function goTo(nextStep) { setMessage(''); setStep(nextStep) }

  if (access === 'checking') return <div className="access-loading">Загружаем RAMP…</div>
  if (access === 'allowed') return children(switchUser)

  return <main className="access-page"><section className="access-card">
    <div className="brand">RAMP</div>
    {step === 'login' && <>
      <p className="eyebrow">Добро пожаловать</p>
      <h1>Пандус, рассчитанный для вашего питомца</h1>
      <p className="access-lead">Войдите, чтобы открыть свой кабинет и сохранённые проекты.</p>
      <form className="access-form" onSubmit={submitLogin}>
        <label className="field"><span>Электронная почта</span><input required type="email" autoComplete="email" value={login.email} onChange={(event) => setLogin({ ...login, email: event.target.value })} /></label>
        <label className="field"><span>Пароль</span><input required type="password" autoComplete="current-password" value={login.password} onChange={(event) => setLogin({ ...login, password: event.target.value })} /></label>
        <button className="primary-button" type="submit" disabled={busy}>Войти</button>
      </form>
      <div className="access-actions">
        <button className="secondary-button" type="button" onClick={() => goTo('register')}>Зарегистрироваться</button>
        <button className="secondary-button guest-entry-button" type="button" onClick={continueAsGuest}>Посмотреть без регистрации</button>
        <button className="admin-entry-button" type="button" onClick={() => goTo('admin')}>Я администратор</button>
      </div>
      <small>Без регистрации можно пользоваться конструктором, но нельзя сохранять проекты и отправлять заказ.</small>
    </>}
    {step === 'register' && <form className="access-form" onSubmit={submitRegistration}>
      <p className="eyebrow">Первый вход</p><h2>Регистрация</h2>
      <label className="field"><span>Имя</span><input required maxLength="120" autoComplete="name" value={registration.name} onChange={(event) => setRegistration({ ...registration, name: event.target.value })} /></label>
      <label className="field"><span>Электронная почта</span><input required type="email" autoComplete="email" value={registration.email} onChange={(event) => setRegistration({ ...registration, email: event.target.value })} /></label>
      <label className="field"><span>Пароль (не менее 10 символов)</span><input required type="password" minLength="10" maxLength="128" autoComplete="new-password" value={registration.password} onChange={(event) => setRegistration({ ...registration, password: event.target.value })} /></label>
      <button className="primary-button" type="submit" disabled={busy}>Создать аккаунт</button>
      <button className="link-button" type="button" onClick={() => goTo('login')}>Уже зарегистрированы? Войти</button>
    </form>}
    {step === 'admin' && <form className="access-form" onSubmit={submitAdmin}>
      <p className="eyebrow">Вход администратора</p><h2>Управление RAMP</h2>
      <label className="field"><span>Логин</span><input required autoComplete="username" value={admin.username} onChange={(event) => setAdmin({ ...admin, username: event.target.value })} /></label>
      <label className="field"><span>Пароль</span><input required type="password" autoComplete="current-password" value={admin.password} onChange={(event) => setAdmin({ ...admin, password: event.target.value })} /></label>
      <button className="primary-button" type="submit" disabled={busy}>Войти на главный экран</button>
      <button className="link-button" type="button" onClick={() => goTo('login')}>Назад</button>
    </form>}
    {message && <div className="account-message" role="status">{message}</div>}
  </section></main>
}
