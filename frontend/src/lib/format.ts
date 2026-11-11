// NFR-13: ngày dd/mm/yyyy, giờ 24 giờ. Không đi qua Date để tránh lệch múi giờ.

/** `2026-11-09` -> `09/11/2026`. Giá trị không đúng định dạng được trả nguyên. */
export function formatDate(iso: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso)
  return match ? `${match[3]}/${match[2]}/${match[1]}` : iso
}

/** `09:15:00` -> `09:15`. Giá trị không đúng định dạng được trả nguyên. */
export function formatTime(time: string): string {
  const match = /^(\d{2}):(\d{2})(?::\d{2})?$/.exec(time)
  return match ? `${match[1]}:${match[2]}` : time
}
