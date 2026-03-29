// Bogotá is UTC-5 (no DST)
const BOGOTA_OFFSET_HOURS = -5;

/**
 * Given a local date string (YYYY-MM-DD), returns the UTC ISO 8601 start and end
 * timestamps that bracket the full day in Bogotá time (America/Bogota, UTC-5).
 */
export function bogotaDayRange(dateISO: string): { startISO: string; endISO: string } {
  // Start: YYYY-MM-DDT00:00:00 Bogotá = YYYY-MM-DDT05:00:00Z
  const startLocal = new Date(`${dateISO}T00:00:00`);
  const startUTC = new Date(startLocal.getTime() - BOGOTA_OFFSET_HOURS * 60 * 60 * 1000);

  // End: YYYY-MM-DDT23:59:59 Bogotá = next day T04:59:59Z
  const endLocal = new Date(`${dateISO}T23:59:59`);
  const endUTC = new Date(endLocal.getTime() - BOGOTA_OFFSET_HOURS * 60 * 60 * 1000);

  return {
    startISO: startUTC.toISOString(),
    endISO: endUTC.toISOString(),
  };
}
