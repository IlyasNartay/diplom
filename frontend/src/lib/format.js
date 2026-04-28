const moneyFormatter = new Intl.NumberFormat('ru-RU')
const dateFormatter = new Intl.DateTimeFormat('ru-RU', {
  dateStyle: 'long',
  timeStyle: 'short'
})

export function formatMoney(value) {
  return `${moneyFormatter.format(Number(value || 0))} ₸`
}

export function formatDateTime(value) {
  if (!value) {
    return 'Дата уточняется'
  }

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return dateFormatter.format(parsed)
}

export function normalizeAssetUrl(value, apiBaseUrl) {
  if (!value) {
    return ''
  }
  if (value.startsWith('http://') || value.startsWith('https://')) {
    return value
  }

  const base = (apiBaseUrl || '').replace(/\/$/, '')
  return `${base}${value.startsWith('/') ? value : `/${value}`}`
}

export function sessionPreview(event) {
  const nextSession = [...(event?.sessions || [])]
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))[0]

  if (!nextSession) {
    return 'Сеансы скоро появятся'
  }

  return `${formatDateTime(nextSession.start_time)} · от ${formatMoney(nextSession.price)}`
}
