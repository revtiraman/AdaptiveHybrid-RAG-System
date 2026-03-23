import { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';

type GraphNode = { id: string; group: number; depth: number };
type GraphLink = { source: string; target: string };

const allNodes: GraphNode[] = [
  { id: 'paper', group: 1, depth: 0 },
  { id: 'transformer', group: 2, depth: 1 },
  { id: 'wmt', group: 3, depth: 1 },
  { id: 'attention', group: 2, depth: 2 },
  { id: 'sequence-modeling', group: 2, depth: 2 },
  { id: 'bleu-score', group: 3, depth: 2 },
  { id: 'inference-speed', group: 4, depth: 3 },
  { id: 'long-context', group: 4, depth: 3 },
];

const allLinks: GraphLink[] = [
  { source: 'paper', target: 'transformer' },
  { source: 'paper', target: 'wmt' },
  { source: 'transformer', target: 'attention' },
  { source: 'transformer', target: 'sequence-modeling' },
  { source: 'wmt', target: 'bleu-score' },
  { source: 'attention', target: 'inference-speed' },
  { source: 'sequence-modeling', target: 'long-context' },
];

const groups = [1, 2, 3, 4];

function nodeColor(group: number): string {
  if (group === 1) return '#1d4ed8';
  if (group === 2) return '#0ea5e9';
  if (group === 3) return '#f59e0b';
  return '#16a34a';
}

export function KnowledgeGraphViewer() {
  const ref = useRef<SVGSVGElement | null>(null);
  const [query, setQuery] = useState('');
  const [maxDepth, setMaxDepth] = useState(3);
  const [enabledGroups, setEnabledGroups] = useState<number[]>(groups);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const nodeSet = new Set(
      allNodes
        .filter((node) => node.depth <= maxDepth && enabledGroups.includes(node.group))
        .filter((node) => !q || node.id.toLowerCase().includes(q))
        .map((node) => node.id),
    );

    const nodes = allNodes.filter((node) => nodeSet.has(node.id));
    const links = allLinks.filter((link) => nodeSet.has(link.source) && nodeSet.has(link.target));
    return { nodes, links };
  }, [enabledGroups, maxDepth, query]);

  useEffect(() => {
    if (!ref.current) return;
    const width = ref.current.clientWidth || 860;
    const height = ref.current.clientHeight || 560;
    const nodes = filtered.nodes.map((node) => ({ ...node }));
    const links = filtered.links.map((link) => ({ ...link }));

    const svg = d3.select(ref.current);
    svg.selectAll('*').remove();

    if (!nodes.length) {
      svg
        .append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', '#64748b')
        .text('No nodes match current filters');
      return;
    }

    const sim = d3
      .forceSimulation(nodes as never)
      .force('link', d3.forceLink(links as never).id((d: never) => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-240))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const link = svg
      .append('g')
      .attr('stroke', '#94a3b8')
      .selectAll('line')
      .data(links)
      .join('line');

    const node = svg
      .append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', (d) => 11 + (3 - d.depth))
      .attr('fill', (d) => nodeColor(d.group));

    const label = svg
      .append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text((d) => d.id)
      .attr('font-size', 12)
      .attr('fill', '#0f172a');

    sim.on('tick', () => {
      link
        .attr('x1', (d: never) => d.source.x)
        .attr('y1', (d: never) => d.source.y)
        .attr('x2', (d: never) => d.target.x)
        .attr('y2', (d: never) => d.target.y);

      node.attr('cx', (d: never) => d.x).attr('cy', (d: never) => d.y);
      label.attr('x', (d: never) => d.x + 18).attr('y', (d: never) => d.y + 4);
    });

    return () => {
      sim.stop();
    };
  }, [filtered]);

  return (
    <div className="h-full p-4">
      <div className="grid h-full grid-rows-[auto_1fr] gap-3 rounded-lg border border-slate-300 bg-surface-primary p-3">
        <div className="grid gap-2 md:grid-cols-[1fr_auto_auto]">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            className="rounded-md border border-slate-300 px-2 py-1 text-sm outline-none"
            placeholder="Search node"
          />
          <label className="flex items-center gap-2 rounded-md border border-slate-300 px-2 py-1 text-xs text-text-secondary">
            Depth {maxDepth}
            <input
              type="range"
              min={0}
              max={3}
              value={maxDepth}
              onChange={(event) => setMaxDepth(Number(event.target.value))}
            />
          </label>
          <button
            onClick={() => {
              setQuery('');
              setMaxDepth(3);
              setEnabledGroups(groups);
            }}
            className="rounded-md border border-slate-300 px-2 py-1 text-xs"
          >
            Reset filters
          </button>
        </div>
        <div className="flex min-h-0 gap-3">
          <div className="hidden w-36 shrink-0 rounded-md border border-slate-300 p-2 md:block">
            <div className="mb-2 text-xs font-semibold">Node groups</div>
            <div className="space-y-2">
              {groups.map((group) => {
                const enabled = enabledGroups.includes(group);
                return (
                  <label key={group} className="flex items-center gap-2 text-xs text-text-secondary">
                    <input
                      type="checkbox"
                      checked={enabled}
                      onChange={() =>
                        setEnabledGroups((prev) =>
                          enabled ? prev.filter((value) => value !== group) : [...prev, group],
                        )
                      }
                    />
                    <span className="inline-flex h-2 w-2 rounded-full" style={{ backgroundColor: nodeColor(group) }} />
                    Group {group}
                  </label>
                );
              })}
            </div>
          </div>
          <div className="min-h-0 flex-1 rounded-md border border-slate-300 p-2">
            <svg ref={ref} className="h-full w-full" />
          </div>
        </div>
      </div>
    </div>
  );
}
