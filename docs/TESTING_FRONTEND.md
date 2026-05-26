# Frontend Testing

Guide for linting, building, and extending tests in the AI Film Studio Next.js frontend.

## Current Testing Surface

The frontend currently uses two verification steps:

1. **ESLint** &mdash; static analysis for TypeScript and Next.js conventions.
2. **Next.js build** &mdash; TypeScript type checking and production compilation.

Both steps run in CI (see [CI Testing](TESTING_CI.md)).

## Running Checks

```bash
cd frontend
npm install          # first time only

# Lint
npm run lint

# Build (includes TypeScript type checking)
npm run build
```

## ESLint Configuration

The project uses ESLint flat config (`eslint.config.mjs`) with:

- `@eslint/js` recommended rules
- `@typescript-eslint` for TypeScript-specific checks
- `@next/eslint-plugin-next` for Next.js best practices

Key rule overrides:

| Rule | Setting | Reason |
|---|---|---|
| `@typescript-eslint/no-unused-vars` | warn (ignore `_` prefix) | Allow intentional unused params |
| `@typescript-eslint/no-explicit-any` | off | Flexibility during rapid development |
| `@next/next/no-img-element` | off | Allow native `<img>` when needed |

Ignored directories: `.next/`, `node_modules/`, `out/`.

## Project Structure for Testing

```
frontend/
├── app/
│   ├── page.tsx              # Landing page
│   ├── layout.tsx            # Root layout
│   ├── providers.tsx         # React Query provider
│   ├── create/page.tsx       # Film creation form
│   ├── dashboard/page.tsx    # Project dashboard
│   ├── login/                # Login page
│   ├── register/             # Registration page
│   ├── projects/             # Project views
│   ├── scripts/              # Script management
│   ├── storyboards/          # Storyboard views
│   ├── scenes/               # Scene management
│   └── voiceovers/           # Voiceover management
├── components/
│   └── Sidebar.tsx           # Navigation sidebar
└── eslint.config.mjs
```

## Adding Unit Tests

The project does not yet include a JavaScript/TypeScript test runner. To add component and utility tests:

### Option A: Vitest (Recommended for Vite/Next.js)

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
```

Add to `package.json`:

```json
{
  "scripts": {
    "test": "vitest run",
    "test:watch": "vitest"
  }
}
```

Create `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './tests/setup.ts',
  },
})
```

Create `tests/setup.ts`:

```typescript
import '@testing-library/jest-dom'
```

### Option B: Jest

```bash
npm install -D jest @testing-library/react @testing-library/jest-dom ts-jest @types/jest
```

Add `jest.config.ts`:

```typescript
import type { Config } from 'jest'
import nextJest from 'next/jest'

const createJestConfig = nextJest({ dir: './' })

const config: Config = {
  testEnvironment: 'jsdom',
  setupFilesAfterSetup: ['<rootDir>/tests/setup.ts'],
}

export default createJestConfig(config)
```

## Writing Component Tests

Example using React Testing Library (works with either Vitest or Jest):

```typescript
// tests/components/Sidebar.test.tsx
import { render, screen } from '@testing-library/react'
import Sidebar from '@/components/Sidebar'

describe('Sidebar', () => {
  it('renders navigation links', () => {
    render(<Sidebar />)
    expect(screen.getByText('Dashboard')).toBeInTheDocument()
    expect(screen.getByText('Create')).toBeInTheDocument()
  })
})
```

## Writing Utility Tests

```typescript
// tests/lib/format.test.ts
import { formatDuration } from '@/lib/format'

describe('formatDuration', () => {
  it('formats seconds into mm:ss', () => {
    expect(formatDuration(90)).toBe('1:30')
  })
})
```

## Snapshot Testing

For verifying that rendered UI does not change unexpectedly:

```typescript
import { render } from '@testing-library/react'
import Home from '@/app/page'

it('matches snapshot', () => {
  const { container } = render(<Home />)
  expect(container).toMatchSnapshot()
})
```

Run `npm test -- -u` to update snapshots after intentional changes.

## Accessibility Testing

Add `@axe-core/react` for runtime accessibility audits:

```bash
npm install -D @axe-core/react
```

```typescript
import { axe, toHaveNoViolations } from 'jest-axe'
expect.extend(toHaveNoViolations)

it('has no accessibility violations', async () => {
  const { container } = render(<Home />)
  const results = await axe(container)
  expect(results).toHaveNoViolations()
})
```

## TypeScript Strict Mode

The build step (`npm run build`) runs TypeScript type checking. Any type errors will fail the build and CI. This serves as a type-level test suite for the entire frontend codebase.
