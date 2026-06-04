const moneyFormatter = new Intl.NumberFormat('ru-RU')

export function formatMoney(value) {
  return `${moneyFormatter.format(Number(value || 0))} ₸`
}

export function formatDateTime(value, locale = 'ru-RU') {
  if (!value) {
    return locale.startsWith('en') ? 'Date TBD' : 'Дата уточняется'
  }

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'long',
    timeStyle: 'short'
  }).format(parsed)
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

export function sessionPreview(event, locale = 'ru-RU') {
  const nextSession = [...(event?.sessions || [])]
    .sort((a, b) => new Date(a.start_time) - new Date(b.start_time))[0]

  if (!nextSession) {
    return locale.startsWith('en') ? 'Sessions coming soon' : 'Сеансы скоро появятся'
  }

  const fromWord = locale.startsWith('en') ? 'from' : 'от'
  return `${formatDateTime(nextSession.start_time, locale)} · ${fromWord} ${formatMoney(nextSession.price)}`
}
