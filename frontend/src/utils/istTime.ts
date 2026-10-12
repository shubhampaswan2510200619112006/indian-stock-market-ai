// Authoritative Indian Standard Time (IST) utility
// IST is permanently UTC+05:30 (no Daylight Saving Time).
// Using direct UTC millisecond arithmetic ensures 100% accuracy on every OS, browser, and timezone.

const IST_OFFSET_MS = 5.5 * 60 * 60 * 1000; // 19,800,000 ms

export interface ISTTimeData {
  epochMs: number;
  hours: number;         // 0 - 23 in IST
  minutes: number;       // 0 - 59 in IST
  seconds: number;       // 0 - 59 in IST
  millis: number;        // 0 - 999
  dayOfWeek: number;     // 0 = Sunday, 1 = Monday, ..., 6 = Saturday
  dateNumber: number;    // 1 - 31
  monthName: string;     // Jan, Feb, Oct...
  year: number;          // 2026
  timeString: string;    // "16:25:30" (24-hour)
  timeWithMillis: string;// "16:25:30.482"
  timeString12: string;  // "04:25:30 PM"
  dateString: string;    // "Mon, 12 Oct 2026"
  fullFormatted: string; // "12 Oct 2026 • 16:25:30.482 IST"
  isMarketOpen: boolean;
  session: 'PRE_MARKET' | 'OPEN' | 'CLOSING' | 'CLOSED';
  sessionLabel: string;
  nextEventLabel: string;
}

const MONTH_NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export function getISTTime(date: Date = new Date()): ISTTimeData {
  const epochMs = date.getTime();
  // Calculate exact IST timestamp by shifting UTC epoch
  const istShifted = new Date(epochMs + IST_OFFSET_MS);

  const hours = istShifted.getUTCHours();
  const minutes = istShifted.getUTCMinutes();
  const seconds = istShifted.getUTCSeconds();
  const millis = istShifted.getUTCMilliseconds();
  const dayOfWeek = istShifted.getUTCDay();
  const dateNumber = istShifted.getUTCDate();
  const monthIndex = istShifted.getUTCMonth();
  const year = istShifted.getUTCFullYear();

  const hh = String(hours).padStart(2, '0');
  const mm = String(minutes).padStart(2, '0');
  const ss = String(seconds).padStart(2, '0');
  const mmm = String(millis).padStart(3, '0');

  const timeString = `${hh}:${mm}:${ss}`;
  const timeWithMillis = `${hh}:${mm}:${ss}.${mmm}`;

  // 12-hour format with AM/PM
  const h12 = hours % 12 || 12;
  const ampm = hours >= 12 ? 'PM' : 'AM';
  const timeString12 = `${String(h12).padStart(2, '0')}:${mm}:${ss} ${ampm}`;

  const monthName = MONTH_NAMES[monthIndex];
  const dayName = DAY_NAMES[dayOfWeek];
  const dateString = `${dayName}, ${dateNumber} ${monthName} ${year}`;
  const fullFormatted = `${dateString} • ${timeWithMillis} IST`;

  // NSE Market Sessions:
  // Weekdays only (Monday = 1 through Friday = 5)
  // 09:00 - 09:15 IST: Pre-market auction
  // 09:15 - 15:30 IST: LIVE REGULAR TRADING SESSION (Market Open)
  // 15:30 - 15:40 IST: Post-market closing
  // 15:40 - 09:00 IST: Market Closed (AMO Active)
  const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
  const totalMinutes = hours * 60 + minutes;

  let isMarketOpen = false;
  let session: ISTTimeData['session'] = 'CLOSED';
  let sessionLabel = 'MARKET CLOSED';
  let nextEventLabel = '';

  if (isWeekend) {
    session = 'CLOSED';
    sessionLabel = 'MARKET CLOSED (WEEKEND)';
    nextEventLabel = 'Opens Monday 09:15 AM IST';
  } else {
    if (totalMinutes >= 540 && totalMinutes < 555) {
      // 09:00 to 09:15 IST
      session = 'PRE_MARKET';
      sessionLabel = 'PRE-MARKET AUCTION (09:00 - 09:15 IST)';
      isMarketOpen = false;
      const minsLeft = 555 - totalMinutes;
      nextEventLabel = `Market opens in ${minsLeft}m`;
    } else if (totalMinutes >= 555 && totalMinutes < 930) {
      // 09:15 to 15:30 IST
      session = 'OPEN';
      sessionLabel = 'LIVE MARKET OPEN (09:15 - 15:30 IST)';
      isMarketOpen = true;
      const minsLeft = 930 - totalMinutes;
      nextEventLabel = `Closes in ${Math.floor(minsLeft / 60)}h ${minsLeft % 60}m`;
    } else if (totalMinutes >= 930 && totalMinutes < 940) {
      // 15:30 to 15:40 IST
      session = 'CLOSING';
      sessionLabel = 'MARKET CLOSED (POST-MARKET SESSION)';
      isMarketOpen = false;
      nextEventLabel = 'Closed for the day';
    } else {
      // Before 09:00 or after 15:40 IST
      session = 'CLOSED';
      sessionLabel = 'MARKET CLOSED (SESSION ENDED 15:30 IST)';
      isMarketOpen = false;
      if (hours >= 15) {
        nextEventLabel = 'Opens tomorrow 09:15 AM IST';
      } else {
        const minsToOpen = 555 - totalMinutes;
        nextEventLabel = `Opens at 09:15 AM (${Math.floor(minsToOpen / 60)}h ${minsToOpen % 60}m)`;
      }
    }
  }

  return {
    epochMs,
    hours,
    minutes,
    seconds,
    millis,
    dayOfWeek,
    dateNumber,
    monthName,
    year,
    timeString,
    timeWithMillis,
    timeString12,
    dateString,
    fullFormatted,
    isMarketOpen,
    session,
    sessionLabel,
    nextEventLabel,
  };
}
