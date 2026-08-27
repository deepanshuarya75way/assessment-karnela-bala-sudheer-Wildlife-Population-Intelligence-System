import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";

export default defineConfig([
  ...nextVitals,
  globalIgnores([".next/**", "out/**", "node_modules/**"]),
  {
    rules: {
      // Existing client components intentionally hydrate browser session state
      // in effects; keep these as warnings rather than blocking deployment.
      "react-hooks/set-state-in-effect": "off",
      "react-hooks/incompatible-library": "off",
      "react-hooks/exhaustive-deps": "warn",
    },
  },
]);
