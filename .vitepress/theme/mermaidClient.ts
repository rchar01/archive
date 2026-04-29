type MermaidApi = typeof import('mermaid').default

let mermaidPromise: Promise<MermaidApi> | null = null
let diagramSequence = 0

export async function loadMermaid(): Promise<MermaidApi> {
  if (!mermaidPromise) {
    mermaidPromise = import('mermaid').then((module) => module.default)
  }

  return mermaidPromise
}

export function nextMermaidDiagramId(): string {
  diagramSequence += 1
  return `mermaid-diagram-${diagramSequence}`
}
