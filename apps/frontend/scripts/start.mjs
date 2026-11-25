// Standalone builds omit static assets; copy them beside the generated server.
import { cpSync, existsSync } from "node:fs";
const staticSource = new URL("../.next/static/", import.meta.url);
const staticTarget = new URL(
  "../.next/standalone/.next/static/",
  import.meta.url,
);
const server = new URL("../.next/standalone/server.js", import.meta.url);
if (!existsSync(server)) throw new Error("Run npm run build before npm start.");
cpSync(staticSource, staticTarget, { recursive: true });
process.env.HOSTNAME = process.env.FRONTEND_HOST || "127.0.0.1";
process.env.PORT = process.env.PORT || "3000";
await import(server.href);
