import pluginVue from "eslint-plugin-vue";
import tseslint from "typescript-eslint";

// "flat/essential" (correctness) en vez de "flat/recommended": este
// proyecto no usa Prettier (no está en la sección 13 del prompt maestro),
// así que no tiene sentido que ESLint discuta formato de línea con nadie.
export default tseslint.config(
  { ignores: ["dist/**", "node_modules/**"] },
  ...tseslint.configs.recommended,
  ...pluginVue.configs["flat/essential"],
  {
    files: ["**/*.vue"],
    languageOptions: {
      parserOptions: { parser: tseslint.parser },
    },
  },
  {
    rules: {
      "vue/multi-word-component-names": "off",
    },
  },
);
