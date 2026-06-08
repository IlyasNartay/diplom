export const CITY_COORDINATES = {
  Almaty: { lat: 43.238949, lon: 76.889709 },
  Astana: { lat: 51.160523, lon: 71.470356 },
  Konaev: { lat: 43.86681, lon: 77.06304 },
  Kaskelen: { lat: 43.2047, lon: 76.6278 }
}

export function normalizeCityName(city) {
  return city?.name_en || city?.name_ru || ''
}
