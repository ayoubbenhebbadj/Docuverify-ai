import test from 'node:test'
import assert from 'node:assert/strict'
import {
  normalizeApiUrl,
  resolveApiBaseUrl,
  DEFAULT_DEV_API_URL,
  DEFAULT_PROD_API_URL,
} from '../src/services/api.ts'

test('normalizeApiUrl removes trailing slashes and redundant /api', () => {
  assert.equal(normalizeApiUrl('https://example.com/'), 'https://example.com')
  assert.equal(normalizeApiUrl('https://example.com///'), 'https://example.com')
  assert.equal(normalizeApiUrl('https://example.com/api'), 'https://example.com')
  assert.equal(normalizeApiUrl('https://example.com/api/'), 'https://example.com')
  assert.equal(normalizeApiUrl('http://127.0.0.1:8000/api/'), 'http://127.0.0.1:8000')
  assert.equal(normalizeApiUrl(''), '')
  assert.equal(normalizeApiUrl(null), '')
  assert.equal(normalizeApiUrl(undefined), '')
})

test('resolveApiBaseUrl prefers VITE_API_URL when provided', () => {
  const result = resolveApiBaseUrl(
    'https://docuverify-backend-l6g7.onrender.com',
    'http://127.0.0.1:8000',
    false
  )
  assert.equal(result, 'https://docuverify-backend-l6g7.onrender.com')
})

test('resolveApiBaseUrl strips /api from VITE_API_URL', () => {
  const result = resolveApiBaseUrl(
    'https://docuverify-backend-l6g7.onrender.com/api/',
    null,
    false
  )
  assert.equal(result, 'https://docuverify-backend-l6g7.onrender.com')
})

test('resolveApiBaseUrl falls back to VITE_API_BASE_URL if VITE_API_URL is missing', () => {
  const result = resolveApiBaseUrl(
    undefined,
    'https://custom-backend.example.com',
    false
  )
  assert.equal(result, 'https://custom-backend.example.com')
})

test('resolveApiBaseUrl defaults to production Render backend in production mode', () => {
  const result = resolveApiBaseUrl(undefined, undefined, false)
  assert.equal(result, DEFAULT_PROD_API_URL)
  assert.equal(result, 'https://docuverify-backend-l6g7.onrender.com')
})

test('resolveApiBaseUrl defaults to local development backend in dev mode', () => {
  const result = resolveApiBaseUrl(undefined, undefined, true)
  assert.equal(result, DEFAULT_DEV_API_URL)
  assert.equal(result, 'http://127.0.0.1:8000')
})

