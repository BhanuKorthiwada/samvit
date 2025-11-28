import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import pluginReact from "eslint-plugin-react";
import json from "@eslint/json";
import markdown from "@eslint/markdown";
// import css from "@eslint/css";
import { defineConfig, globalIgnores } from "eslint/config";
import { tanstackConfig } from '@tanstack/eslint-config'

export default defineConfig([
  globalIgnores([".config/","**/src/components/**/*.*"]),
  ...tanstackConfig,
  { files: ["**/*.{js,mjs,cjs,ts,mts,cts,jsx,tsx}"], ignores: ["**/src/components/**/*.*"], plugins: { js }, extends: ["js/recommended"], languageOptions: { globals: globals.browser } },
  tseslint.configs.recommended,
  pluginReact.configs.flat['jsx-runtime'],
  { files: ["**/*.json"], plugins: { json }, language: "json/json", extends: ["json/recommended"] },
  { files: ["**/*.jsonc"], plugins: { json }, language: "json/jsonc", extends: ["json/recommended"] },
  { files: ["**/*.md"], plugins: { markdown }, language: "markdown/gfm", extends: ["markdown/recommended"] },
  // { files: ["**/*.css"], plugins: { css }, language: "css/css", extends: ["css/recommended"] },
]);
