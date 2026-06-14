// ESLint 9 flat config — reglas mínimas y sensatas para el MVP.
export default [
  {
    files: ['src/**/*.js'],
    languageOptions: {
      ecmaVersion: 2023,
      sourceType: 'module',
    },
    rules: {
      'no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': 'warn',
      'prefer-const': 'error',
      eqeqeq: ['error', 'always'],
    },
  },
];
