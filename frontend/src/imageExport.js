export function collectPageStyles(options, styleSheets = document.styleSheets) {
  let css = ''
  for (const sheet of styleSheets) {
    try { css += [...sheet.cssRules].map((rule) => rule.cssText).join('\n') } catch { /* inaccessible external stylesheet */ }
  }
  if (!options.showLabels) css += '\nsvg text{display:none!important}'
  if (!options.showDimensions) css += '\n.offset-line,.dimension-cap,.control-line,.mechanics-label,.point-label,.key-point{display:none!important}'
  return css
}

export function buildExportSvg(container, options, styleSheets) {
  const sourceSvgs = [...container.querySelectorAll('.diagram-card svg')]
  if (!sourceSvgs.length) throw new Error('Нет SVG для экспорта.')
  const [outputWidth, outputHeight] = options.aspect === '1:1' ? [1000, 1000] : [1200, 900]
  const columns = sourceSvgs.length > 1 ? 2 : 1
  const rows = Math.ceil(sourceSvgs.length / columns)
  const naturalWidth = columns * 700; const naturalHeight = rows * 410
  const nested = sourceSvgs.map((svg, index) => {
    const x = (index % columns) * 700; const y = Math.floor(index / columns) * 410
    return `<svg x="${x}" y="${y}" width="700" height="410" viewBox="${svg.getAttribute('viewBox') || '0 0 700 410'}">${svg.innerHTML}</svg>`
  }).join('')
  const scale = Math.min(outputWidth / naturalWidth, outputHeight / naturalHeight) * (options.scale / 100)
  const x = (outputWidth - naturalWidth * scale) / 2; const y = (outputHeight - naturalHeight * scale) / 2
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${outputWidth}" height="${outputHeight}" viewBox="0 0 ${outputWidth} ${outputHeight}"><style>${collectPageStyles(options, styleSheets)}</style><rect width="100%" height="100%" fill="${options.background}"/><g transform="translate(${x} ${y}) scale(${scale})">${nested}</g></svg>`
}

export function svgToPngBlob(source, environment = {}) {
  const makeUrl = environment.createObjectURL || URL.createObjectURL
  const revokeUrl = environment.revokeObjectURL || URL.revokeObjectURL
  const createImage = environment.createImage || (() => new Image())
  const createCanvas = environment.createCanvas || (() => document.createElement('canvas'))
  return new Promise((resolve, reject) => {
    const url = makeUrl(new Blob([source], { type: 'image/svg+xml;charset=utf-8' })); const image = createImage()
    image.onload = () => {
      const canvas = createCanvas(); canvas.width = image.width; canvas.height = image.height
      canvas.getContext('2d').drawImage(image, 0, 0); revokeUrl(url)
      canvas.toBlob((blob) => blob ? resolve(blob) : reject(new Error('Не удалось подготовить PNG.')), 'image/png')
    }
    image.onerror = () => { revokeUrl(url); reject(new Error('Не удалось загрузить SVG для PNG.')) }
    image.src = url
  })
}
