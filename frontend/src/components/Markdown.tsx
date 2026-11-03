import { Fragment, type ReactNode } from 'react';

/**
 * Minimal, dependency-free Markdown renderer for assistant answers.
 * Supports headings (#, ##, ###), bullet / numbered lists, block quotes,
 * **bold**, *italic* / _italic_, `code` and highlights citation markers like [1].
 * Builds React elements directly (no innerHTML), so model output can't inject HTML.
 */
function renderInline(text: string, keyPrefix: string): ReactNode[] {
  const pattern = /(\*\*[^*\n]+\*\*|`[^`\n]+`|\[\d+\]|\*[^*\n]+\*|\b_[^_\n]+_\b)/g;
  const parts = text.split(pattern).filter((p) => p !== undefined && p !== '');
  return parts.map((part, i) => {
    const key = `${keyPrefix}-${i}`;
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={key} className="font-bold text-ink">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={key} className="rounded bg-mist px-1 py-0.5 text-[0.85em]">{part.slice(1, -1)}</code>;
    }
    if (/^\[\d+\]$/.test(part)) {
      return (
        <sup key={key} className="mx-0.5 rounded bg-chakra-tint px-1 text-[0.7em] font-bold text-chakra">
          {part.slice(1, -1)}
        </sup>
      );
    }
    if ((part.startsWith('*') && part.endsWith('*')) || (part.startsWith('_') && part.endsWith('_'))) {
      return <em key={key} className="text-ink-mute">{part.slice(1, -1)}</em>;
    }
    return <Fragment key={key}>{part}</Fragment>;
  });
}

export default function Markdown({ content }: { content: string }) {
  const lines = (content || '').replace(/\r/g, '').split('\n');
  const blocks: ReactNode[] = [];
  let list: { ordered: boolean; items: string[] } | null = null;

  const flushList = () => {
    if (!list) return;
    const items = list.items.map((item, i) => (
      <li key={i} className="leading-relaxed">{renderInline(item, `li-${blocks.length}-${i}`)}</li>
    ));
    blocks.push(
      list.ordered ? (
        <ol key={`ol-${blocks.length}`} className="ml-5 list-decimal space-y-1">{items}</ol>
      ) : (
        <ul key={`ul-${blocks.length}`} className="ml-5 list-disc space-y-1 marker:text-chakra">{items}</ul>
      ),
    );
    list = null;
  };

  lines.forEach((raw, idx) => {
    const line = raw.trimEnd();
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);

    if (bullet || numbered) {
      const ordered = Boolean(numbered && !bullet);
      if (!list || list.ordered !== ordered) {
        flushList();
        list = { ordered, items: [] };
      }
      list.items.push((bullet ?? numbered)![1]);
      return;
    }
    flushList();

    if (!line.trim()) return;
    const heading = line.match(/^(#{1,4})\s+(.*)$/);
    if (heading) {
      const size = heading[1].length <= 2 ? 'text-base' : 'text-sm';
      blocks.push(
        <p key={`h-${idx}`} className={`${size} mt-2 font-bold text-ink`}>
          {renderInline(heading[2], `h-${idx}`)}
        </p>,
      );
      return;
    }
    if (line.startsWith('>')) {
      blocks.push(
        <div key={`q-${idx}`} className="rounded-lg border-l-2 border-marigold bg-marigold-tint px-3 py-2 text-ink-soft">
          {renderInline(line.replace(/^>\s?/, ''), `q-${idx}`)}
        </div>,
      );
      return;
    }
    blocks.push(
      <p key={`p-${idx}`} className="leading-relaxed">
        {renderInline(line, `p-${idx}`)}
      </p>,
    );
  });
  flushList();

  return <div className="space-y-2">{blocks}</div>;
}
