# Dependency Audit

Date: 2026-06-23

Command:

```bash
npm audit --json
```

Result:

- 1 low advisory.
- 2 moderate advisories.
- No high or critical advisories.

## Findings

| Package | Severity | Source | Runtime impact | Safe fix applied | Rationale |
| --- | --- | --- | --- | --- | --- |
| `esbuild@0.27.7` | Low | Transitive through `vitest -> vite` | Dev/test tooling only. The advisory affects a local development server scenario on Windows; this frontend production build is served by Next, not Vite. | No | `vitest@3.2.6` resolves `vite@7.3.5`, and that Vite line requires `esbuild ^0.27.0`. Forcing `esbuild@0.28.1` would override a `0.x` minor dependency outside Vite's declared range. Upgrading Vitest to the next major line would be dependency churn for a dev-only advisory. |
| `postcss@8.4.31` | Moderate | Nested inside `next@15.5.19` | Production dependency because it is bundled under Next. Practical exposure is limited to CSS stringification paths controlled by Next/build tooling, not user-supplied CSS in this app. | No | `npm audit` reports the only available fix as `next@9.3.3`, a semver-major downgrade and invalid remediation for this Next 15 app. Current `next@16.2.9` still declares `postcss 8.4.31`, so there is no safe patch-level Next update that removes the advisory. |
| `next@15.5.19` | Moderate | Aggregate advisory via nested `postcss` | Same as above. | No | The Next advisory is the parent effect of the nested PostCSS advisory. `npm audit fix --force` would downgrade Next and violate the Phase 2B constraints. |

## Commands Reviewed

```bash
npm ls esbuild postcss next --all
npm audit fix --dry-run --json
npm view vite@7 version dependencies.esbuild --json
npm view vitest@3 version dependencies.vite --json
npm view next version dependencies.postcss --json
```

Latest reviewed output on 2026-06-23:

- `npm audit --json`: 1 low, 2 moderate, 0 high, 0 critical.
- `npm ls esbuild postcss next --all`: `next@15.5.19` carries nested `postcss@8.4.31`; project-level PostCSS is `8.5.15`; `vitest@3.2.6 -> vite@7.3.5 -> esbuild@0.27.7`.
- `npm audit fix --dry-run --json`: does not produce a safe dependency change; the Next/PostCSS fix path remains a semver-major downgrade to `next@9.3.3`.
- `npm view next version dependencies.postcss --json`: latest `next@16.2.9` still declares `postcss 8.4.31`.

## Decision

No dependency changes were applied. The available fixes either require unsafe overrides across `0.x` package boundaries, major tooling upgrades, or an invalid Next downgrade. Revisit after Vite/Vitest or Next publish compatible releases that resolve the advisories without major churn.
