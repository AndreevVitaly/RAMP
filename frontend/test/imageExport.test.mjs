import assert from 'node:assert/strict'
import test from 'node:test'
import { buildExportSvg, svgToPngBlob } from '../src/imageExport.js'

test('SVG export respects 1:1 format and current drawing', () => {
  const svg = { innerHTML: '<polygon points="0,0 1,1"/>', getAttribute: () => '0 0 700 410' }
  const container = { querySelectorAll: () => [svg] }
  const result = buildExportSvg(container, { aspect: '1:1', scale: 100, background: '#ffffff', showLabels: true, showDimensions: true }, [])
  assert.match(result, /width="1000" height="1000"/)
  assert.match(result, /<polygon points="0,0 1,1"\/>/)
})

test('PNG export renders SVG through a canvas', async () => {
  const image = { width: 1000, height: 1000, onload: null, onerror: null, set src(value) { this._src = value; queueMicrotask(() => this.onload()) } }
  const png = new Blob(['png'], { type: 'image/png' })
  const canvas = { getContext: () => ({ drawImage: () => {} }), toBlob: (callback) => callback(png) }
  const result = await svgToPngBlob('<svg/>', { createObjectURL: () => 'blob:test', revokeObjectURL: () => {}, createImage: () => image, createCanvas: () => canvas })
  assert.equal(result.type, 'image/png')
})
