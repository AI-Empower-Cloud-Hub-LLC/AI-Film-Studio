import js from "@eslint/js";
import tsPlugin from "@typescript-eslint/eslint-plugin";
import tsParser from "@typescript-eslint/parser";
import nextPlugin from "@next/eslint-plugin-next";

export default [
  js.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaFeatures: { jsx: true },
      },
      globals: {
        React: "readonly",
        JSX: "readonly",
        window: "readonly",
        document: "readonly",
        localStorage: "readonly",
        fetch: "readonly",
        console: "readonly",
        setTimeout: "readonly",
        clearTimeout: "readonly",
        setInterval: "readonly",
        clearInterval: "readonly",
        process: "readonly",
        URL: "readonly",
        WebSocket: "readonly",
        HTMLElement: "readonly",
        HTMLInputElement: "readonly",
        HTMLTextAreaElement: "readonly",
        HTMLSelectElement: "readonly",
        HTMLFormElement: "readonly",
        HTMLButtonElement: "readonly",
        HTMLDivElement: "readonly",
        Event: "readonly",
        FormData: "readonly",
        RequestInit: "readonly",
        Response: "readonly",
        Headers: "readonly",
        AbortController: "readonly",
        alert: "readonly",
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
      "@next/next": nextPlugin,
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,
      ...nextPlugin.configs.recommended.rules,
      "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
      "@typescript-eslint/no-explicit-any": "off",
      "@next/next/no-img-element": "off",
      "no-unused-vars": "off",
    },
  },
  {
    files: ["**/*.js"],
    languageOptions: {
      globals: {
        module: "readonly",
        process: "readonly",
        require: "readonly",
        __dirname: "readonly",
      },
    },
  },
  {
    ignores: [".next/", "node_modules/", "out/"],
  },
];
