export const CUSTOMER_TOKEN_KEY = 'ramp_customer_token'
export const GUEST_ACCESS_KEY = 'ramp_guest_access'
export const ADMIN_TOKEN_KEY = 'ramp_admin_token'

export function clearAccessStorage(local = localStorage, session = sessionStorage) {
  local.removeItem(CUSTOMER_TOKEN_KEY)
  session.removeItem(GUEST_ACCESS_KEY)
  session.removeItem(ADMIN_TOKEN_KEY)
}
