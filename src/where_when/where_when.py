"""Get information about right here, right now."""
# SPDX-FileCopyrightText: 2026 Grzegorz Grzęda
# SPDX-License-Identifier: MIT

from argparse import ArgumentParser
import requests
from astral import LocationInfo, sun, moon
from timezonefinder import TimezoneFinder
from datetime import datetime
from zoneinfo import ZoneInfo


def parse_arguments():
    parser = ArgumentParser(
        description="Get information about right here, right now.")
    parser.add_argument('location', type=str,
                        help='Location for which to get sun and moon info')
    parser.add_argument(
        '--date', type=str, help='Date for which to get the information (YYYY-MM-DD)')
    parser.add_argument(
        '--time', type=str, help='Time for which to get the information (HH:MM:SS)')

    return parser.parse_args()


def get_moon_phase_name(phase):
    phases = [
        "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
        "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"
    ]
    index = int((phase + 3.69) / 7.38) % 8
    return phases[index]


def get_day_duration(sunrise, sunset):
    duration = sunset - sunrise
    return duration


def print_day_duration(sunrise, sunset):
    duration = get_day_duration(sunrise, sunset)
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"Day Duration: {hours}h {minutes}m {seconds}s")


def get_shortest_day():
    return datetime(datetime.now().year, 12, 21)


def get_longest_day():
    return datetime(datetime.now().year, 6, 21)


def get_shortest_day_duration(city):
    shortest_day = get_shortest_day()
    s = sun.sun(city.observer, date=shortest_day)
    return get_day_duration(s['sunrise'], s['sunset'])


def get_longest_day_duration(city):
    longest_day = get_longest_day()
    s = sun.sun(city.observer, date=longest_day)
    return get_day_duration(s['sunrise'], s['sunset'])


def print_day_duration(city, sunrise, sunset):
    duration = get_day_duration(sunrise, sunset)
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    print(f"Day Duration in {city.name}: {hours}h {minutes}m {seconds}s")
    shortest_day_duration = get_shortest_day_duration(city)
    longest_day_duration = get_longest_day_duration(city)

    def format_diff(delta):
        total_minutes = int(delta.total_seconds() // 60)
        hours, minutes = divmod(total_minutes, 60)
        parts = []
        if hours:
            parts.append(f"{hours}h")
        if minutes or not parts:
            parts.append(f"{minutes}m")
        return " ".join(parts)

    if duration == longest_day_duration:
        print("This is the longest day of the year!")
        print("Day is longer than shortest day by: "
              f"{format_diff(duration - shortest_day_duration)}")
    elif duration == shortest_day_duration:
        print("This is the shortest day of the year!")
        print("Day is shorter than longest day by: "
              f"{format_diff(longest_day_duration - duration)}")
    else:
        print("Day is shorter than longest day by: "
              f"{format_diff(longest_day_duration - duration)}")
        print("Day is longer than shortest day by: "
              f"{format_diff(duration - shortest_day_duration)}")


def main():
    args = parse_arguments()
    location = args.location
    date = args.date
    time = args.time

    if date is None:
        date = datetime.now().strftime('%Y.%m.%d')
    if time is None:
        time = datetime.now().strftime('%H:%M:%S')

    print(
        f"Retrieving sun and moon information for location: {location}, date: {date}, time: {time}")

    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": location, "format": "json", "limit": 1},
            headers={"User-Agent": "sun-moon-info-script"}
        )
        response.raise_for_status()
        results = response.json()
        if results:
            coords = results[0]
            print(f"Latitude: {coords['lat']}, Longitude: {coords['lon']}")
        else:
            print("Could not determine coordinates for the given location.")

        city, country = location.split(
            ",") if "," in location else (location, "")

        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=coords['lon'], lat=coords['lat'])
        print(f"Timezone: {timezone_str}")

        city = LocationInfo(city, country,
                            timezone_str, float(coords['lat']), float(coords['lon']))

        date = datetime.strptime(date, '%Y.%m.%d').date()
        s = sun.sun(city.observer, date=date)
        m = moon.phase(date)
        m_rise = moon.moonrise(city.observer, date=date)
        m_set = moon.moonset(city.observer, date=date)

        if isinstance(city.timezone, str):
            city.timezone = ZoneInfo(city.timezone)
        s_rise = s['sunrise'].astimezone(
            city.timezone).strftime('%Y.%m.%d %H:%M:%S')
        s_set = s['sunset'].astimezone(
            city.timezone).strftime('%Y.%m.%d %H:%M:%S')
        m_rise = m_rise.astimezone(city.timezone).strftime('%Y.%m.%d %H:%M:%S')
        m_set = m_set.astimezone(city.timezone).strftime('%Y.%m.%d %H:%M:%S')

        print(f"Sunrise: {s_rise}, Sunset: {s_set}")
        print(
            f"Moonrise: {m_rise}, Moonset: {m_set}, Moon Phase: {get_moon_phase_name(m)}")

        print_day_duration(city, s['sunrise'], s['sunset'])

    except requests.RequestException as exc:
        print(f"Failed to retrieve coordinates: {exc}")


if __name__ == "__main__":
    main()
