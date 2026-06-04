$ErrorActionPreference = 'Stop'

$catalogBaseUrl = if ($env:CATALOG_BASE_URL) { $env:CATALOG_BASE_URL.TrimEnd('/') } else { 'http://localhost:8005' }
$seatBaseUrl = if ($env:SEAT_BASE_URL) { $env:SEAT_BASE_URL.TrimEnd('/') } else { 'http://localhost:8001' }
$frontendBaseUrl = if ($env:FRONTEND_BASE_URL) { $env:FRONTEND_BASE_URL.TrimEnd('/') } else { 'http://localhost:3000' }

function Invoke-JsonGet {
    param([string]$Url)
    return Invoke-RestMethod -Method Get -Uri $Url
}

function Invoke-JsonPost {
    param(
        [string]$Url,
        [hashtable]$Body
    )

    return Invoke-RestMethod -Method Post -Uri $Url -ContentType 'application/json' -Body ($Body | ConvertTo-Json -Depth 8)
}

function Invoke-JsonPut {
    param(
        [string]$Url,
        [hashtable]$Body
    )

    return Invoke-RestMethod -Method Put -Uri $Url -ContentType 'application/json' -Body ($Body | ConvertTo-Json -Depth 8)
}

function Normalize-DateKey {
    param([string]$Value)
    return ([DateTimeOffset]::Parse($Value)).ToString('yyyy-MM-ddTHH:mm')
}

$categories = @(
    @{ key = 'concert'; name_ru = 'Концерты'; name_en = 'Concerts'; name_kz = 'Концерттер' },
    @{ key = 'festival'; name_ru = 'Фестивали'; name_en = 'Festivals'; name_kz = 'Фестивальдер' },
    @{ key = 'classical'; name_ru = 'Классика'; name_en = 'Classical'; name_kz = 'Классика' }
)

$cities = @(
    @{ key = 'almaty'; name_ru = 'Алматы'; name_en = 'Almaty'; name_kz = 'Алматы' },
    @{ key = 'astana'; name_ru = 'Астана'; name_en = 'Astana'; name_kz = 'Астана' },
    @{ key = 'konaev'; name_ru = 'Конаев'; name_en = 'Konaev'; name_kz = 'Қонаев' }
)

$eventsToSeed = @(
    @{
        title = '«Gul Almaty» Concert'
        description = 'Реальное событие по листингу Freedom Ticketon: концерт «Gul Almaty» в Казахской государственной филармонии имени Жамбыла.'
        category = 'classical'
        city = 'almaty'
        poster = 'gul-almaty.svg'
        session = @{ start_time = '2026-05-01T15:00:00+05:00'; hall_name = 'Kazakh State Philharmonic named after Zhambyl'; price = 1500 }
        seats = @{ rows = 6; seats_per_row = 10 }
    },
    @{
        title = 'Gazizkhan Shekerbek'
        description = 'Реальное событие по листингу Freedom Ticketon: большой концерт Gazizkhan Shekerbek в Almaty Arena.'
        category = 'concert'
        city = 'almaty'
        poster = 'gazizkhan-shekerbek.svg'
        session = @{ start_time = '2026-05-02T19:30:00+05:00'; hall_name = 'Almaty Arena'; price = 5000 }
        seats = @{ rows = 7; seats_per_row = 12 }
    },
    @{
        title = 'Epic of Valor'
        description = 'Реальное событие по листингу Freedom Ticketon: праздничный концерт симфонического оркестра «Epic of Valor» в Астане.'
        category = 'classical'
        city = 'astana'
        poster = 'epic-of-valor.svg'
        session = @{ start_time = '2026-05-08T19:00:00+05:00'; hall_name = 'E. Rakhmadiev State Academic Philharmonic Concert Hall'; price = 3000 }
        seats = @{ rows = 6; seats_per_row = 11 }
    },
    @{
        title = 'Jah Khalib - CADS 2026'
        description = 'Реальное событие по листингу Freedom Ticketon: концерт Jah Khalib как afterparty первого этапа CADS 2026 в Konaev.'
        category = 'concert'
        city = 'konaev'
        poster = 'jah-khalib-cads.svg'
        session = @{ start_time = '2026-05-09T20:00:00+05:00'; hall_name = 'ASP Arena'; price = 10000 }
        seats = @{ rows = 8; seats_per_row = 12 }
    },
    @{
        title = 'SOLΛNA in Astana'
        description = 'Реальное событие по листингу Freedom Ticketon: международный фестиваль SOLΛNA First Season в Astana Golf Club.'
        category = 'festival'
        city = 'astana'
        poster = 'solana-astana.svg'
        session = @{ start_time = '2026-05-17T19:00:00+05:00'; hall_name = 'Astana Golf Club'; price = 62820 }
        seats = @{ rows = 10; seats_per_row = 14 }
    },
    @{
        title = 'KOVACS'
        description = 'Реальное событие по листингу Freedom Ticketon: международный концерт KOVACS в клубе MOTOR в Алматы.'
        category = 'concert'
        city = 'almaty'
        poster = 'kovacs.svg'
        session = @{ start_time = '2026-05-29T20:00:00+05:00'; hall_name = 'MOTOR Club'; price = 23000 }
        seats = @{ rows = 7; seats_per_row = 10 }
    },
    @{
        title = 'Beu Fest Almaty 2026'
        description = 'Реальное событие по листингу Freedom Ticketon: юбилейный Beu Fest в комплексе «Сункар» в Алматы.'
        category = 'festival'
        city = 'almaty'
        poster = 'beu-fest.svg'
        session = @{ start_time = '2026-06-06T18:00:00+05:00'; hall_name = 'Trump facilities «Sunkar»'; price = 16000 }
        seats = @{ rows = 9; seats_per_row = 12 }
    }
)

$categoryMap = @{}
$existingCategories = @(Invoke-JsonGet "$catalogBaseUrl/categories")
foreach ($category in $categories) {
    $found = $existingCategories | Where-Object { $_.name_en -eq $category.name_en -or $_.name_ru -eq $category.name_ru } | Select-Object -First 1
    if (-not $found) {
        $found = Invoke-JsonPost "$catalogBaseUrl/admin/categories" @{
            name_ru = $category.name_ru
            name_en = $category.name_en
            name_kz = $category.name_kz
        }
        Write-Host "Created category: $($category.name_ru)"
    } else {
        Write-Host "Using category: $($category.name_ru)"
    }
    $categoryMap[$category.key] = $found.id
}

$cityMap = @{}
$existingCities = @(Invoke-JsonGet "$catalogBaseUrl/cities")
foreach ($city in $cities) {
    $found = $existingCities | Where-Object { $_.name_en -eq $city.name_en -or $_.name_ru -eq $city.name_ru } | Select-Object -First 1
    if (-not $found) {
        $found = Invoke-JsonPost "$catalogBaseUrl/admin/cities" @{
            name_ru = $city.name_ru
            name_en = $city.name_en
            name_kz = $city.name_kz
        }
        Write-Host "Created city: $($city.name_ru)"
    } else {
        Write-Host "Using city: $($city.name_ru)"
    }
    $cityMap[$city.key] = $found.id
}

$existingEventPayload = Invoke-JsonGet "$catalogBaseUrl/events?limit=1000"
$existingEvents = @($existingEventPayload.events)

foreach ($eventItem in $eventsToSeed) {
    $eventBody = @{
        title = $eventItem.title
        description = $eventItem.description
        poster_url = "$frontendBaseUrl/demo-posters/$($eventItem.poster)"
        category_id = $categoryMap[$eventItem.category]
        city_id = $cityMap[$eventItem.city]
    }

    $eventRecord = $existingEvents | Where-Object { $_.title -eq $eventItem.title } | Select-Object -First 1
    if (-not $eventRecord) {
        $eventRecord = Invoke-JsonPost "$catalogBaseUrl/admin/events" $eventBody
        $existingEvents += $eventRecord
        Write-Host "Created event: $($eventItem.title)"
    } else {
        Invoke-JsonPut "$catalogBaseUrl/admin/events/$($eventRecord.id)" @{
            title = $eventItem.title
            description = $eventItem.description
            poster_url = "$frontendBaseUrl/demo-posters/$($eventItem.poster)"
            video_url = $null
        } | Out-Null
        $eventRecord = Invoke-JsonGet "$catalogBaseUrl/events/$($eventRecord.id)"
        Write-Host "Updated event: $($eventItem.title)"
    }

    $targetSessionKey = Normalize-DateKey $eventItem.session.start_time
    $existingSession = @($eventRecord.sessions) | Where-Object {
        (Normalize-DateKey $_.start_time) -eq $targetSessionKey -and $_.hall_name -eq $eventItem.session.hall_name
    } | Select-Object -First 1

    if (-not $existingSession) {
        $existingSession = Invoke-JsonPost "$catalogBaseUrl/admin/events/$($eventRecord.id)/sessions" $eventItem.session
        Write-Host "  Added session: $($eventItem.session.hall_name)"
    } else {
        Invoke-JsonPut "$catalogBaseUrl/admin/sessions/$($existingSession.id)" @{
            hall_name = $eventItem.session.hall_name
            price = $eventItem.session.price
        } | Out-Null
        Write-Host "  Synced session: $($eventItem.session.hall_name)"
    }

    $seats = @(Invoke-JsonGet "$seatBaseUrl/seats/$($existingSession.id)")
    if ($seats.Count -eq 0) {
        Invoke-JsonPost "$seatBaseUrl/admin/seats/generate/$($existingSession.id)" $eventItem.seats | Out-Null
        Write-Host "  Generated seats: rows=$($eventItem.seats.rows), perRow=$($eventItem.seats.seats_per_row)"
    } else {
        Write-Host "  Seats already exist: $($seats.Count)"
    }
}

Write-Host ''
Write-Host 'Demo events have been seeded successfully.'
