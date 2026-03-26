import path from "node:path"
import { reactRouter } from "@react-router/dev/vite"
import tailwindcss from "@tailwindcss/vite"
import { defineConfig } from "vite"
import tsconfigPaths from "vite-tsconfig-paths"

export default defineConfig({
  plugins: [tailwindcss(), reactRouter(), tsconfigPaths()],
  resolve: {
    alias: {
      "~": path.resolve(__dirname, "app"),
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (!id.includes("node_modules")) {
            return undefined
          }

          if (
            id.includes("@react-three/drei") ||
            id.includes("@react-three/fiber") ||
            id.includes("node_modules\\three\\") ||
            id.includes("/node_modules/three/")
          ) {
            return "three-vendor"
          }

          if (id.includes("framer-motion")) {
            return "motion-vendor"
          }

          if (id.includes("@hugeicons")) {
            return "icons-vendor"
          }

          return undefined
        },
      },
    },
  },
})
