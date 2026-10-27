const SVG_STYLE_PROPERTIES = [
  'fill', 'fill-opacity', 'stroke', 'stroke-opacity', 'stroke-width', 'stroke-dasharray',
  'stroke-linecap', 'stroke-linejoin', 'font-family', 'font-size', 'font-weight', 'text-anchor',
]

export async function captureRampProfile() {
  const source = document.querySelector('.pdf-profile-source svg[data-ramp-profile]') || document.querySelector('svg[data-ramp-profile]')
  if (!source) throw new Error('Геометрический профиль ещё не сформирован.')

  const clone = source.cloneNode(true)
  const sourceNodes = [source, ...source.querySelectorAll('*')]
  const cloneNodes = [clone, ...clone.querySelectorAll('*')]
  sourceNodes.forEach((node, index) => {
    const computed = getComputedStyle(node)
    const target = cloneNodes[index]
    for (const property of SVG_STYLE_PROPERTIES) target.style.setProperty(property, computed.getPropertyValue(property))
  })
  clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
  clone.setAttribute('width', '1440')
  clone.setAttribute('height', '860')

  const blob = new Blob([new XMLSerializer().serializeToString(clone)], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  try {
    const image = await new Promise((resolve, reject) => {
      const element = new Image()
      element.onload = () => resolve(element)
      element.onerror = () => reject(new Error('Не удалось подготовить изображение профиля.'))
      element.src = url
    })
    const canvas = document.createElement('canvas')
    canvas.width = 1440
    canvas.height = 860
    const context = canvas.getContext('2d')
    context.fillStyle = '#ffffff'
    context.fillRect(0, 0, canvas.width, canvas.height)
    context.drawImage(image, 0, 0, canvas.width, canvas.height)
    return canvas.toDataURL('image/png')
  } finally {
    URL.revokeObjectURL(url)
  }
}
