// Shim for Node.js builds without zstd support (undici/jsdom compatibility)
// jsdom@31 depends on undici@8 which calls zlib.createZstdDecompress at load time.
// Node.js builds compiled without zstd support have createZstdDecompress === undefined,
// causing a TypeError. Define a no-op so undici loads successfully.
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const zlib = require('node:zlib');
if (typeof zlib.createZstdDecompress === 'undefined') {
  zlib.createZstdDecompress = () => {
    throw new Error('zstd not supported in this Node.js build');
  };
}
