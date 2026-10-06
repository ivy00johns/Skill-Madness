// One headless Freebuff-engine run for run_eval.py's freebuff host.
//
// Reads one JSON request on stdin, runs Freebuff's root agent (snapshot) with
// the Codebuff SDK from a pinned source checkout, and writes JSON Lines to
// stdout: one `init`, every SDK event as-is, then one terminal `result`.
// Scoring happens in Python; this script only reports what happened.
//
// Why source and not npm: the published @codebuff/sdk requires a paid Codebuff
// API key. BYOK (any OpenAI-compatible endpoint, no Codebuff account) exists
// only in the source tree, so the checkout is a declared dependency.
//
// Request fields: query, cwd, skillsDir, model, baseUrl, provider
// ("openai-compatible" | "openrouter"), apiKeyEnv, maxAgentSteps, timeoutMs,
// codebuffDir, snapshotPath.
import { randomUUID } from 'node:crypto'
import { readFileSync } from 'node:fs'
import path from 'node:path'

const emit = (event: Record<string, unknown>) => process.stdout.write(JSON.stringify(event) + '\n')

// The SDK validates these public build values at import. BYOK runs make no
// Codebuff, analytics or billing request, so placeholders are enough; the
// analytics host points at a closed local port so nothing could leave anyway.
const PLACEHOLDER_ENV: Record<string, string> = {
  NEXT_PUBLIC_CB_ENVIRONMENT: 'prod',
  NEXT_PUBLIC_CODEBUFF_APP_URL: 'https://www.codebuff.com',
  NEXT_PUBLIC_SUPPORT_EMAIL: 'support@codebuff.com',
  NEXT_PUBLIC_POSTHOG_API_KEY: 'disabled',
  NEXT_PUBLIC_POSTHOG_HOST_URL: 'http://127.0.0.1:9',
  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY: 'disabled',
  NEXT_PUBLIC_STRIPE_CUSTOMER_PORTAL: 'http://127.0.0.1:9',
  NEXT_PUBLIC_WEB_PORT: '3000',
}

async function main(): Promise<number> {
  const request = JSON.parse(readFileSync(0, 'utf8'))
  for (const key of ['query', 'cwd', 'skillsDir', 'model', 'baseUrl', 'provider', 'apiKeyEnv', 'codebuffDir', 'snapshotPath']) {
    if (typeof request[key] !== 'string' || !request[key]) throw new Error(`request.${key} is required`)
  }
  if (!['openai-compatible', 'openrouter'].includes(request.provider)) throw new Error('provider must be openai-compatible or openrouter')
  const apiKey = process.env[request.apiKeyEnv]
  if (!apiKey) throw new Error(`environment variable ${request.apiKeyEnv} is empty`)
  // The SDK redacts the key's value from every string it handles; a short key
  // (e.g. "k") turns the `skill` tool name into `s[redacted]ill` and every call fails.
  if (apiKey.length < 12) throw new Error(`${request.apiKeyEnv} is too short (under 12 characters) to be redacted safely`)
  for (const [key, value] of Object.entries(PLACEHOLDER_ENV)) process.env[key] ??= value

  const snapshot = JSON.parse(readFileSync(request.snapshotPath, 'utf8'))
  const definition = { ...snapshot.definition, model: request.model }
  const { CodebuffClient } = await import(path.join(request.codebuffDir, 'sdk/src/index.ts'))

  const now = new Date().toISOString()
  const byok = {
    id: randomUUID(), revision: 1, name: 'skill-creator eval', provider: request.provider,
    model: request.model, baseUrl: request.baseUrl, credentialRef: `env:${request.apiKeyEnv}`,
    createdAt: now, updatedAt: now,
  }
  Object.defineProperty(byok, 'apiKey', { value: apiKey, enumerable: false })

  emit({ type: 'init', model: request.model, agent: definition.id, snapshot_commit: snapshot.source_commit })
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), Number(request.timeoutMs) || 60000)
  try {
    const client = new CodebuffClient({ byok, cwd: request.cwd, disableAgentRegistry: true })
    const state = await client.run({
      agent: definition.id,
      agentDefinitions: [definition],
      prompt: request.query,
      skillsDir: request.skillsDir,
      maxAgentSteps: Number(request.maxAgentSteps) || 3,
      signal: controller.signal,
      handleEvent: (event: Record<string, unknown>) => emit(event),
    })
    const output = state?.output as { type?: string; message?: string } | undefined
    if (controller.signal.aborted) {
      emit({ type: 'result', exit_code: 1, error: 'timeout' })
      return 1
    }
    if (output?.type === 'error') {
      emit({ type: 'result', exit_code: 1, error: output.message ?? 'run error' })
      return 1
    }
    emit({ type: 'result', exit_code: 0, error: null })
    return 0
  } finally {
    clearTimeout(timer)
  }
}

main().then((code) => process.exit(code), (error) => {
  emit({ type: 'result', exit_code: 1, error: String(error?.message ?? error) })
  process.exit(1)
})
