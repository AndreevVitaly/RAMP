import assert from 'node:assert/strict'
import test from 'node:test'

import { ADMIN_TOKEN_KEY, clearAccessStorage, CUSTOMER_TOKEN_KEY, GUEST_ACCESS_KEY } from '../src/accessSession.js'

function storage(initial) {
  const values = new Map(Object.entries(initial))
  return {
    getItem(key) { return values.get(key) ?? null },
    removeItem(key) { values.delete(key) },
  }
}

test('switching users clears customer, guest and admin access', () => {
  const local = storage({ [CUSTOMER_TOKEN_KEY]: 'customer-token', unrelated: 'keep' })
  const session = storage({ [GUEST_ACCESS_KEY]: 'true', [ADMIN_TOKEN_KEY]: 'admin-token' })

  clearAccessStorage(local, session)

  assert.equal(local.getItem(CUSTOMER_TOKEN_KEY), null)
  assert.equal(session.getItem(GUEST_ACCESS_KEY), null)
  assert.equal(session.getItem(ADMIN_TOKEN_KEY), null)
  assert.equal(local.getItem('unrelated'), 'keep')
})
