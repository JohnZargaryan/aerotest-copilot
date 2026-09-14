import { build, createServer, preview } from "vite";

// Vite treats # in resolved source paths as a URL fragment in dev mode.
// Production builds work here, so keep this workspace usable without moving it.
if (process.cwd().includes("#")) {
  console.log("This path contains #. Building a local preview instead of hot reload.");
  console.log("After editing, run npm run build in another terminal and refresh the page.");
  await build();
  const server = await preview({
    preview: { host: "127.0.0.1", port: 5173, strictPort: true },
  });
  server.printUrls();
} else {
  const server = await createServer({
    server: { host: "127.0.0.1", port: 5173, strictPort: true },
  });
  await server.listen();
  server.printUrls();
}
