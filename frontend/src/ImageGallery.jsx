import { useEffect, useMemo, useState } from 'react'
import { deleteRampImage, listRampImages, updateRampImage, uploadRampImage } from './api'
import { MATERIALS } from './materials'

const IMAGE_TYPES = {
  product: 'Главный вид изделия', sofa: 'Пандус возле дивана', bed: 'Пандус возле кровати',
  folded: 'Пандус в сложенном состоянии', storage: 'Хранение за мебелью', carpet: 'Крупный план покрытия',
}

export default function ImageGallery({ kind, configuration }) {
  const [items, setItems] = useState([])
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState('')
  const [message, setMessage] = useState('')
  const [fields, setFields] = useState({ title: '', caption: '', description: '', image_type: 'product' })
  const isIllustration = kind === 'illustration'

  async function refresh() { setItems(await listRampImages(kind)) }
  useEffect(() => { refresh().catch((error) => setMessage(error.message)) }, [kind])
  useEffect(() => {
    if (!file) { setPreview(''); return undefined }
    const url = URL.createObjectURL(file); setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const configSnapshot = useMemo(() => ({
    height_cm: configuration.height_cm, ramp_length_cm: configuration.ramp_length_cm,
    width_cm: configuration.width_cm, support_panel_width_cm: configuration.support_panel_width_cm, product_state: configuration.product_state,
  }), [configuration])

  async function submit(event) {
    event.preventDefault(); if (!file) return
    const data = new FormData()
    data.append('kind', kind); data.append('file', file)
    data.append('title', fields.title); data.append('caption', fields.caption); data.append('description', fields.description)
    if (isIllustration) data.append('image_type', fields.image_type)
    data.append('color', configuration.color); data.append('has_slats', configuration.has_slats)
    data.append('side_rails', configuration.side_rails); data.append('configuration', JSON.stringify(configSnapshot))
    try {
      await uploadRampImage(data); setFile(null); setFields({ title: '', caption: '', description: '', image_type: 'product' }); setMessage('Изображение сохранено.'); await refresh()
    } catch (error) { setMessage(error.message) }
  }

  async function remove(id) { await deleteRampImage(id); await refresh() }
  async function makePrimary(id) { await updateRampImage(id, { is_primary: true }); await refresh() }

  return <div className="gallery-workspace">
    <form className="image-upload" onSubmit={submit}>
      <label className="field"><span>Файл JPG, PNG или WebP</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => setFile(event.target.files[0] || null)} /></label>
      {preview && <img className="upload-preview" src={preview} alt="Предварительный просмотр" />}
      {isIllustration && <label className="field"><span>Название</span><input value={fields.title} onChange={(event) => setFields({ ...fields, title: event.target.value })} /></label>}
      {isIllustration && <label className="field"><span>Тип изображения</span><select value={fields.image_type} onChange={(event) => setFields({ ...fields, image_type: event.target.value })}>{Object.entries(IMAGE_TYPES).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>}
      {!isIllustration && <label className="field"><span>Подпись</span><input value={fields.caption} onChange={(event) => setFields({ ...fields, caption: event.target.value })} /></label>}
      <label className="field"><span>Описание</span><textarea value={fields.description} onChange={(event) => setFields({ ...fields, description: event.target.value })} /></label>
      <small>Привязка: {MATERIALS[configuration.color]?.label}, рейки — {configuration.has_slats ? 'есть' : 'нет'}, бортики — {configuration.side_rails ? 'есть' : 'нет'}.</small>
      <button className="primary-button" type="submit" disabled={!file}>Загрузить</button>
      {message && <p className="gallery-message">{message}</p>}
    </form>
    <div className="image-gallery">
      {items.length === 0 && <p>Изображений пока нет.</p>}
      {items.map((item) => <article key={item.id} className={`gallery-item ${item.is_primary ? 'primary' : ''}`}>
        <img src={item.file} alt={item.title || item.caption || 'Изображение пандуса'} />
        <div><strong>{item.title || item.caption || item.original_name}</strong>{item.is_illustration && <span className="illustration-badge">Иллюстрация</span>}<small>{MATERIALS[item.color]?.label || 'Цвет не указан'} · {item.has_slats ? 'с рейками' : 'без реек'} · {item.side_rails ? 'с бортиками' : 'без бортиков'}</small><small>{item.configuration?.height_cm ? `${item.configuration.height_cm} × ${item.configuration.ramp_length_cm} × ${item.configuration.width_cm} см` : 'Точные размеры не привязаны'}</small></div>
        <div className="gallery-actions"><button type="button" onClick={() => makePrimary(item.id)} disabled={item.is_primary}>{item.is_primary ? 'Главное' : 'Сделать главным'}</button><button type="button" onClick={() => remove(item.id)}>Удалить</button></div>
      </article>)}
    </div>
  </div>
}
