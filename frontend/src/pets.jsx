export const PET_BREEDS = {
  dachshund: { label: 'Такса', height_cm: 23, length_cm: 55, front_width_cm: 20, image: '/dogs/dachshund.webp', frontImage: '/dogs/dachshund-front.webp' },
  corgi: { label: 'Корги', height_cm: 30, length_cm: 58, front_width_cm: 25, image: '/dogs/corgi.webp', frontImage: '/dogs/corgi-front.webp' },
  pomeranian: { label: 'Шпиц', height_cm: 24, length_cm: 34, front_width_cm: 22, image: '/dogs/pomeranian.webp', frontImage: '/dogs/pomeranian-front.webp' },
  beagle: { label: 'Бигль', height_cm: 38, length_cm: 63, front_width_cm: 26, image: '/dogs/beagle.webp', frontImage: '/dogs/beagle-front.webp' },
  french_bulldog: { label: 'Французский бульдог', height_cm: 31, length_cm: 48, front_width_cm: 28, image: '/dogs/french-bulldog.webp', frontImage: '/dogs/french-bulldog-front.webp' },
  labrador: { label: 'Лабрадор', height_cm: 57, length_cm: 90, front_width_cm: 38, image: '/dogs/labrador.webp', frontImage: '/dogs/labrador-front.webp' },
  german_shepherd: { label: 'Немецкая овчарка', height_cm: 62, length_cm: 96, front_width_cm: 40, image: '/dogs/german-shepherd.webp', frontImage: '/dogs/german-shepherd-front.webp' },
}

export function petPreset(breed) {
  const item = PET_BREEDS[breed] || PET_BREEDS.dachshund
  return { breed, height_cm: item.height_cm, length_cm: item.length_cm, front_width_cm: item.front_width_cm }
}

export function DogSilhouette({ pet, x, groundY, heightPx, view = 'side', facing = 1, className = '' }) {
  if (!pet?.enabled) return null
  const breed = PET_BREEDS[pet.breed] || PET_BREEDS.dachshund
  const physicalWidth = view === 'front' ? breed.front_width_cm : pet.length_cm
  const ratio = Math.max(.45, Number(physicalWidth) / Math.max(Number(pet.height_cm), 1))
  const width = heightPx * ratio
  const imageY = view === 'top' ? groundY - heightPx / 2 : groundY - heightPx
  const transform = facing === -1 ? `translate(${x + width} 0) scale(-1 1)` : undefined
  return <g className={`pet-silhouette ${className}`} transform={transform} pointerEvents="none">
    <title>{breed.label}: {breed.height_cm} см в холке</title>
    <image href={view === 'front' ? breed.frontImage : breed.image} x={facing === -1 ? 0 : x} y={imageY} width={width} height={heightPx} preserveAspectRatio="xMidYMax meet" />
  </g>
}
