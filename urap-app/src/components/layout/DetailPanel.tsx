interface DetailPanelProps {
  lead?: {
    name: string;
    title: string;
    company: string;
    email: string;
    globalStatus: string;
  };
}

export function DetailPanel({ lead }: DetailPanelProps) {
  if (!lead) {
    return (
      <aside className="w-80 bg-gray-900 border-l border-gray-800 flex items-center justify-center text-gray-600 text-sm">
        Select a lead to view details
      </aside>
    );
  }

  return (
    <aside className="w-80 bg-gray-900 border-l border-gray-800 flex flex-col">
      <div className="p-4 border-b border-gray-800">
        <div className="font-semibold text-white">{lead.name}</div>
        <div className="text-sm text-gray-400">{lead.title}</div>
        <div className="text-sm text-gray-400">{lead.company}</div>
        <span className="inline-block mt-2 px-2 py-0.5 text-xs rounded-full bg-indigo-900 text-indigo-300">
          {lead.globalStatus}
        </span>
      </div>
      <div className="flex border-b border-gray-800">
        {['Contact', 'Activity', 'Campaigns'].map(tab => (
          <button
            key={tab}
            className="flex-1 py-2 text-xs text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
          >
            {tab}
          </button>
        ))}
      </div>
      <div className="p-4 text-sm text-gray-300">
        <div className="mb-2 font-medium text-gray-400">Contact Details</div>
        <div>{lead.email}</div>
      </div>
    </aside>
  );
}
