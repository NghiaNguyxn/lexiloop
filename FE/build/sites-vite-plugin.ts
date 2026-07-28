import { access, cp, mkdir, rm, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import type { Plugin } from "vite";

async function exists(path: string): Promise<boolean> {
  try {
    await access(path);
    return true;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return false;
    }
    throw error;
  }
}

const workerSource = `
const worker = {
  async fetch(request, env) {
    const response = await env.ASSETS.fetch(request);
    const acceptsHtml = request.headers.get("accept")?.includes("text/html");

    if (response.status === 404 && request.method === "GET" && acceptsHtml) {
      const indexUrl = new URL("/index.html", request.url);
      return env.ASSETS.fetch(new Request(indexUrl, request));
    }

    return response;
  },
};

export default worker;
`.trimStart();

// Packages a Vite SPA in the directory layout expected by Sites.
export function sites(): Plugin {
  let root = process.cwd();

  return {
    name: "lexiloop-sites-package",
    apply: "build",
    configResolved(config) {
      root = config.root;
    },
    async closeBundle() {
      const distDirectory = resolve(root, "dist");
      const metadataDirectory = resolve(distDirectory, ".openai");
      const serverDirectory = resolve(distDirectory, "server");
      const hostingConfig = resolve(root, ".openai", "hosting.json");

      await rm(metadataDirectory, { recursive: true, force: true });
      await mkdir(metadataDirectory, { recursive: true });
      await mkdir(serverDirectory, { recursive: true });

      if (await exists(hostingConfig)) {
        await cp(hostingConfig, resolve(metadataDirectory, "hosting.json"));
      }

      await writeFile(resolve(serverDirectory, "index.js"), workerSource, "utf8");
    },
  };
}
