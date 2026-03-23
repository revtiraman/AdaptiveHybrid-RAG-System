type Props = {
  onPickPrompt: (prompt: string) => void;
};

const prompts = [
  'What is the main contribution of this paper?',
  'Compare the training objectives across papers',
  'What datasets were used in the experiments?',
  'What are the limitations acknowledged?',
];

export function EmptyState({ onPickPrompt }: Props) {
  return (
    <div className="mx-auto mt-12 w-full max-w-3xl rounded-xl border border-slate-300 bg-surface-primary p-6">
      <h3 className="text-lg font-semibold">No chat messages yet</h3>
      <p className="mt-1 text-sm text-text-secondary">Start by asking a paper-grounded question or choose a suggested prompt.</p>
      <div className="mt-4 grid gap-2">
        {prompts.map((prompt) => (
          <button
            key={prompt}
            className="rounded-md border border-slate-300 px-3 py-2 text-left text-sm hover:bg-surface-secondary"
            onClick={() => onPickPrompt(prompt)}
          >
            {prompt}
          </button>
        ))}
      </div>
    </div>
  );
}
