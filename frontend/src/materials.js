export const MATERIALS = {
  dark_gray: { label: 'Тёмно-серый', color: '#4a4f55' },
  light_gray: { label: 'Светло-серый', color: '#aab0b5' },
  black: { label: 'Чёрный', color: '#202226' },
  beige: { label: 'Бежевый', color: '#c7ad85' },
}

export const COLORS = Object.fromEntries(Object.entries(MATERIALS).map(([key, value]) => [key, value.color]))
