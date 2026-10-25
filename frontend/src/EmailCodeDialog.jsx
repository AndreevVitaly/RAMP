import { useEffect, useRef } from 'react'

export default function EmailCodeDialog({ email, code, devCode, message, login = false, onChange, onSubmit, onClose }) {
  const inputRef = useRef(null)
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  useEffect(() => {
    inputRef.current?.focus()
    function onKeyDown(event) {
      if (event.key === 'Escape') onCloseRef.current()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [])

  return <div className="code-dialog-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
    <section className="code-dialog" role="dialog" aria-modal="true" aria-labelledby="code-dialog-title" aria-describedby="code-dialog-description">
      <button className="code-dialog-close" type="button" aria-label="Закрыть окно ввода кода" onClick={onClose}>×</button>
      <p className="eyebrow">Подтверждение почты</p>
      <h2 id="code-dialog-title">Введите код из письма</h2>
      <p id="code-dialog-description">{login ? 'Если адрес зарегистрирован, шестизначный код отправлен на ' : 'Шестизначный код отправлен на '}<strong>{email}</strong>.</p>
      {devCode && <div className="dev-code">Код для локальной разработки: <strong>{devCode}</strong></div>}
      <form className="access-form" onSubmit={onSubmit}>
        <label className="field"><span>Код подтверждения</span><input ref={inputRef} required inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6}" maxLength="6" value={code} onChange={(event) => onChange(event.target.value.replace(/\D/g, ''))} /></label>
        <button className="primary-button" type="submit">Подтвердить и войти</button>
      </form>
      {message && <div className="account-message" role="status">{message}</div>}
      <button className="link-button" type="button" onClick={onClose}>Изменить данные</button>
    </section>
  </div>
}
