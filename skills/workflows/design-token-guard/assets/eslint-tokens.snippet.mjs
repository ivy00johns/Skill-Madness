// design-token-guard — ESLint flat-config block (editor-time fast feedback).
//
// Merge the object below into the project's eslint.config.mjs `export default [ ... ]`
// array. This is the EDITOR layer: it gives in-IDE squiggles for the patterns
// ESLint expresses cleanly. It is deliberately a SUBSET — ESLint can't resolve a
// hex back to its token name, so the authoritative check (with the value→token
// map) stays the Python checker run at pre-commit/CI. Keep both; they're layers,
// not duplicates.
//
// no-restricted-syntax selectors below cover JSX. For Vue/Svelte/Angular
// templates, rely on the pre-commit checker — those need template-aware parsers.

export const designTokenGuardRules = {
  files: ['**/*.{ts,tsx,js,jsx}'],
  rules: {
    'no-restricted-syntax': [
      'error',
      {
        // Hardcoded color literal in JSX inline style: style={{ x: "#abc123" }}
        selector:
          'JSXAttribute[name.name="style"] Literal[value=/#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})\\b|rgba?\\(|hsla?\\(/]',
        message:
          'Hardcoded color in an inline style — use a design token (var(--…)). Run `npm run lint:tokens` for the exact token.',
      },
      {
        // Hardcoded color anywhere in a JSX attribute (fill="#…", color strings)
        selector:
          'JSXAttribute Literal[value=/^#(?:[0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$/]',
        message:
          'Hardcoded color literal — reference a design token instead. Run `npm run lint:tokens`.',
      },
    ],
    // Forbidden utility classes (radius cap / partisan colors). Tune the regex
    // to the project; delete this rule entirely if the project isn't class-based.
    'no-restricted-properties': 'off',
  },
};

// If the project uses tailwindcss with eslint-plugin-tailwindcss, you can ALSO
// forbid radius/partisan utilities at lint time. Example (optional):
//
//   'no-restricted-syntax': [..., {
//     selector: 'Literal[value=/\\brounded-(?:md|lg|xl|2xl|3xl|full)\\b/]',
//     message: 'Radius exceeds the project cap — use the smallest radius token.',
//   }]
