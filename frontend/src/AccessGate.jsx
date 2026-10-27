import { useEffect, useState } from 'react'
import { getAccount, getAdminBriefs, loginAdmin, loginCustomer, registerCustomer, requestLoginCode, verifyEmailCode } from './api'
import { ADMIN_TOKEN_KEY, clearAccessStorage, CUSTOMER_TOKEN_KEY, GUEST_ACCESS_KEY } from './accessSession'

export default function AccessGate({ children }) {
  const [access, setAccess] = useState('checking')
  const [step, setStep] = useState('login')
  const [registration, setRegistration] = useState({ name: '', email: '', password: '' })
  const [login, setLogin] = useState({ email: '', password: '' })
  const [codeEmail, setCodeEmail] = useState('')
  const [code, setCode] = useState('')
  const [admin, setAdmin] = useState({ username: 'admin', password: '' })
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [checkVersion, setCheckVersion] = useState(0)
  const [verifiedCustomer, setVerifiedCustomer] = useState(null)

  useEffect(() => {
    const controller = new AbortController()
    let active = true
    const timeout = setTimeout(() => controller.abort(), 10000)
    const verified = (customer = null) => { if (active) { setVerifiedCustomer(customer); setAccess('allowed') } }
    const failed = (error, key, storage) => {
      if (!active) return
      if (error.status === 401 || error.status === 403) {
        storage.removeItem(key)
        setAccess('gate')
      } else setAccess('unavailable')
    }
    const adminToken = sessionStorage.getItem(ADMIN_TOKEN_KEY)
    if (adminToken) {
      getAdminBriefs(adminToken, controller.signal).then(() => verified()).catch((error) => failed(error, ADMIN_TOKEN_KEY, sessionStorage))
    } else {
      const token = localStorage.getItem(CUSTOMER_TOKEN_KEY)
      if (token) getAccount(token, controller.signal).then(verified).catch((error) => failed(error, CUSTOMER_TOKEN_KEY, localStorage))
      else if (sessionStorage.getItem(GUEST_ACCESS_KEY)) verified()
      else setAccess('gate')
    }
    return () => { active = false; clearTimeout(timeout); controller.abort() }
  }, [checkVersion])

  useEffect(() => {
    function handleStorage(event) {
      if (event.key === CUSTOMER_TOKEN_KEY && event.oldValue && !event.newValue && !sessionStorage.getItem(ADMIN_TOKEN_KEY)) {
        setVerifiedCustomer(null)
        setStep('login')
        setMessage('Войдите в личный кабинет ещё раз.')
        setAccess('gate')
      }
    }
    window.addEventListener('storage', handleStorage)
    return () => window.removeEventListener('storage', handleStorage)
  }, [])

  function enterCustomer(response) {
    localStorage.setItem(CUSTOMER_TOKEN_KEY, response.token)
    sessionStorage.removeItem(GUEST_ACCESS_KEY)
    sessionStorage.removeItem(ADMIN_TOKEN_KEY)
    setVerifiedCustomer(response.customer)
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

  async function submitCodeRequest(event) {
    event.preventDefault(); setMessage(''); setBusy(true)
    try {
      const email = codeEmail.trim()
      const response = await requestLoginCode(email)
      setCodeEmail(email)
      setMessage(response.detail)
      setStep('verify-code')
    } catch (error) { setMessage(error.message) }
    finally { setBusy(false) }
  }

  async function submitCode(event) {
    event.preventDefault(); setMessage(''); setBusy(true)
    try { enterCustomer(await verifyEmailCode(codeEmail, code.trim())) }
    catch (error) { setMessage(error.message) }
    finally { setBusy(false) }
  }

  async function submitAdmin(event) {
    event.preventDefault(); setMessage(''); setBusy(true)
    try {
      const response = await loginAdmin(admin.username, admin.password)
      sessionStorage.setItem(ADMIN_TOKEN_KEY, response.token)
      sessionStorage.removeItem(GUEST_ACCESS_KEY)
      setVerifiedCustomer(null)
      setAccess('allowed')
    } catch (error) { setMessage(error.message) }
    finally { setBusy(false) }
  }

  function continueAsGuest() {
    clearAccessStorage()
    sessionStorage.setItem(GUEST_ACCESS_KEY, 'true')
    setVerifiedCustomer(null)
    setAccess('allowed')
  }

  function switchUser() {
    clearAccessStorage()
    setVerifiedCustomer(null)
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
  if (access === 'allowed') return children(switchUser, verifiedCustomer)
  if (access === 'unavailable') return <main className="access-page"><section className="access-card">
    <div className="brand">RAMP</div>
    <h1>Не удалось проверить вход</h1>
    <p className="access-lead">Соединение с сервером временно недоступно. Ваш вход сохранён.</p>
    <button className="primary-button" type="button" onClick={() => { setAccess('checking'); setCheckVersion((value) => value + 1) }}>Повторить попытку</button>
    <button className="link-button" type="button" onClick={switchUser}>Сменить пользователя</button>
  </section></main>

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
        <button className="secondary-button" type="button" onClick={() => { setCodeEmail(login.email); goTo('request-code') }}>Войти по коду из письма</button>
        <button className="secondary-button guest-entry-button" type="button" onClick={continueAsGuest}>Посмотреть без регистрации</button>
        <button className="admin-entry-button" type="button" onClick={() => goTo('admin')}>Я администратор</button>
      </div>
      <small>Без регистрации можно пользоваться конструктором, но нельзя сохранять проекты и отправлять заказ.</small>
    </>}
    {step === 'request-code' && <form className="access-form" onSubmit={submitCodeRequest}>
      <h2>Вход по коду из письма</h2>
      <p>Для аккаунтов, созданных до появления входа по паролю.</p>
      <label className="field"><span>Электронная почта</span><input required type="email" autoComplete="email" value={codeEmail} onChange={(event) => setCodeEmail(event.target.value)} /></label>
      <button className="primary-button" type="submit" disabled={busy}>Получить код</button>
      <button className="link-button" type="button" onClick={() => goTo('login')}>Назад</button>
    </form>}
    {step === 'verify-code' && <form className="access-form" onSubmit={submitCode}>
      <h2>Введите код из письма</h2>
      <label className="field"><span>Код</span><input required inputMode="numeric" autoComplete="one-time-code" value={code} onChange={(event) => setCode(event.target.value)} /></label>
      <button className="primary-button" type="submit" disabled={busy}>Войти</button>
      <button className="link-button" type="button" onClick={() => goTo('request-code')}>Запросить новый код</button>
    </form>}
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
