// Central configuration. The browser app has no build step; edit here to tune the prototype.
export const CONFIG = Object.freeze({
  apiBase: '/api/v1',
  authTokenKey: 'gvpAuthToken',
  authUserKey: 'gvpAuthUser',
  storageKey: 'gvpHistory',
  zoneKey: 'gvpZonePolygon',
  capture: Object.freeze({ width: 320, height: 180, jpegQuality: 0.6 }),
  monitor: Object.freeze({
    fps: 5,
    changeThreshold: 6,       // heuristic zone-diff percentage that starts a suspected event
    bufferSize: 30,           // rolling frames (~6 s at 5 fps)
    defaultStableSeconds: 2   // scene must be stable this long before evidence is produced
  }),
  analysis: Object.freeze({ threshold: 8 }),
  // Normalised [0..1] rectangle matching the earlier fixed CSS zone overlay.
  defaultPolygon: Object.freeze([
    Object.freeze({ x: 0.17, y: 0.48 }),
    Object.freeze({ x: 0.90, y: 0.48 }),
    Object.freeze({ x: 0.90, y: 0.86 }),
    Object.freeze({ x: 0.17, y: 0.86 })
  ])
});
