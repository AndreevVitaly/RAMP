import { useRef, useState } from 'react'
import ImageGallery from './ImageGallery'
import ProjectionViewer from './ProjectionViewer'
import { buildExportSvg, svgToPngBlob } from './imageExport'

const TABS = [['photos', 'Фотографии'], ['illustrations', 'Иллюстрации'], ['builder', 'Конструктор рисунков']]

function download(blob, name) {
  const url = URL.createObjectURL(blob); const anchor = document.createElement('a')
  anchor.href = url; anchor.download = name; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export default function ImageStudio({ ramp, configuration }) {
  const [tab, setTab] = useState('builder')
  const [view, setView] = useState('axon')
  const [options, setOptions] = useState({ background: '#f4f1e8', showDimensions: true, showLabels: true, scale: 100, theme: 'light', aspect: '4:3' })
  const canvasRef = useRef(null)

  function exportSvg() {
    try { download(new Blob([buildExportSvg(canvasRef.current, options)], { type: 'image/svg+xml;charset=utf-8' }), `ramp-${view}.svg`) } catch (error) { alert(error.message) }
  }

  async function exportPng() {
    try {
      const png = await svgToPngBlob(buildExportSvg(canvasRef.current, options)); download(png, `ramp-${view}.png`)
    } catch (error) { alert(error.message) }
  }

  return <section className="images-module panel">
    <div className="section-heading"><div><p className="eyebrow">Медиатека и визуализация</p><h2>Изображения</h2></div><span>v0.1</span></div>
    <nav className="image-tabs">{TABS.map(([id, label]) => <button type="button" key={id} className={tab === id ? 'active' : ''} onClick={() => setTab(id)}>{label}</button>)}</nav>
    {tab === 'photos' && <ImageGallery kind="photo" configuration={configuration} />}
    {tab === 'illustrations' && <ImageGallery kind="illustration" configuration={configuration} />}
    {tab === 'builder' && <div className="image-builder">
      <div className="image-editor">
        <label>Фон <input type="color" value={options.background} onChange={(event) => setOptions({ ...options, background: event.target.value })} /></label>
        <label>Масштаб <input type="range" min="70" max="130" value={options.scale} onChange={(event) => setOptions({ ...options, scale: Number(event.target.value) })} /><span>{options.scale}%</span></label>
        <label><input type="checkbox" checked={options.showDimensions} onChange={(event) => setOptions({ ...options, showDimensions: event.target.checked })} /> Размеры</label>
        <label><input type="checkbox" checked={options.showLabels} onChange={(event) => setOptions({ ...options, showLabels: event.target.checked })} /> Подписи</label>
        <label>Формат <select value={options.aspect} onChange={(event) => setOptions({ ...options, aspect: event.target.value })}><option>1:1</option><option>4:3</option></select></label>
        <label>Оформление <select value={options.theme} onChange={(event) => setOptions({ ...options, theme: event.target.value })}><option value="light">Светлое</option><option value="dark">Тёмное</option></select></label>
        <button type="button" onClick={exportSvg}>Экспорт SVG</button><button type="button" onClick={exportPng}>Экспорт PNG</button>
      </div>
      <div className={`export-canvas aspect-${options.aspect.replace(':', '-')}`}><ProjectionViewer ramp={ramp} view={view} onViewChange={setView} displayOptions={options} containerRef={canvasRef} /></div>
      <p className="folded-note">Сложенный вид будет добавлен после подтверждения геометрии складывания и положения стойки.</p>
    </div>}
  </section>
}
