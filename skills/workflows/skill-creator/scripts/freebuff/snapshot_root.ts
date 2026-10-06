// Regenerate assets/freebuff-root-agent.json from a Codebuff checkout.
//
// Freebuff's root agent is plain data (no handleSteps), so a snapshot of its
// system prompt and tool list reproduces it exactly. The snapshot uses the
// switches Codebuff's own eval harness uses: noAskUser (an ask_user call would
// stall a headless run) and noWeb (web results can leak the answer).
//
// Usage (from anywhere; needs bun and `bun install` done in the checkout):
//   bun run snapshot_root.ts --codebuff <checkout> --out <file> [--model-const NAME]
//
// Source: https://github.com/CodebuffAI/codebuff (Apache-2.0). The snapshot
// is a derived work; keep the source commit and license fields intact.
import { execFileSync } from 'node:child_process'
import { writeFileSync } from 'node:fs'
import path from 'node:path'

function arg(name: string, fallback?: string): string {
  const index = process.argv.indexOf(name)
  const value = index > -1 ? process.argv[index + 1] : fallback
  if (!value) throw new Error(`missing ${name}`)
  return value
}

const checkout = path.resolve(arg('--codebuff'))
const out = path.resolve(arg('--out'))
const modelConst = arg('--model-const', 'FREEBUFF_DEEPSEEK_V4_FLASH_MODEL_ID')

const { createBase3CliRoot } = await import(path.join(checkout, 'agents/base3.ts'))
const models = await import(path.join(checkout, 'common/src/constants/freebuff-models.ts'))
const model = models[modelConst]
if (typeof model !== 'string') throw new Error(`unknown model constant ${modelConst}`)

const root = createBase3CliRoot({ model, isFreebuff: true, noAskUser: true, noWeb: true })
if (typeof root.handleSteps === 'function') {
  throw new Error('root agent now has handleSteps; a data snapshot would not reproduce it')
}
const commit = execFileSync('git', ['-C', checkout, 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim()

const snapshot = {
  source: 'https://github.com/CodebuffAI/codebuff',
  source_commit: commit,
  license: 'Apache-2.0',
  derived_from: `agents/base3.ts createBase3CliRoot({ model: ${modelConst}, isFreebuff: true, noAskUser: true, noWeb: true })`,
  definition: {
    id: 'freebuff-root-eval',
    displayName: 'Freebuff root (eval snapshot)',
    model,
    toolNames: root.toolNames,
    systemPrompt: root.systemPrompt,
    outputMode: root.outputMode,
    includeMessageHistory: root.includeMessageHistory,
    inputSchema: root.inputSchema,
  },
}
writeFileSync(out, JSON.stringify(snapshot, null, 2) + '\n')
console.log(`wrote ${out} from ${commit.slice(0, 12)} (${root.toolNames.length} tools, ${root.systemPrompt.length} prompt chars)`)
