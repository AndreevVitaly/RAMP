import test from 'node:test'
import assert from 'node:assert/strict'
import { getAccount } from '../src/api.js'

test('account check preserves HTTP status even when server returns HTML', async () => {
  const originalFetch = globalThis.fetch
  try {
    globalThis.fetch = async () => new Response('<html>Unauthorized</html>', { status: 401 })
    await assert.rejects(getAccount('expired'), (error) => error.status === 401)

    globalThis.fetch = async () => new Response('<html>Unavailable</html>', { status: 503 })
    await assert.rejects(getAccount('valid'), (error) => error.status === 503)
  } finally {
    globalThis.fetch = originalFetch
  }
})
