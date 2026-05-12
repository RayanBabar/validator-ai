import React from 'react';
import { Plus, Trash2 } from 'lucide-react';

export function RecursiveEditor({ data, onChange, name = 'Root' }: { data: any, onChange: (newData: any) => void, name?: string }) {
  if (data === null || data === undefined) {
    return (
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-bold text-primary w-32 truncate">{name}:</span>
        <input type="text" value="" onChange={e => onChange(e.target.value)} className="flex-1 bg-secondary/50 rounded px-2 py-1 text-xs" placeholder="null" />
      </div>
    );
  }

  if (typeof data === 'string') {
    return (
      <div className="flex items-start gap-2 mb-2">
        <span className="text-xs font-bold text-primary w-32 shrink-0 truncate pt-1">{name}:</span>
        <textarea 
          value={data} 
          onChange={e => onChange(e.target.value)} 
          className="flex-1 bg-secondary/50 rounded px-2 py-1 text-xs min-h-[60px] resize-y" 
        />
      </div>
    );
  }

  if (typeof data === 'number') {
    return (
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-bold text-primary w-32 truncate">{name}:</span>
        <input type="number" value={data} onChange={e => onChange(Number(e.target.value))} className="flex-1 bg-secondary/50 rounded px-2 py-1 text-xs" />
      </div>
    );
  }
  
  if (typeof data === 'boolean') {
    return (
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-bold text-primary w-32 truncate">{name}:</span>
        <input type="checkbox" checked={data} onChange={e => onChange(e.target.checked)} className="rounded" />
      </div>
    );
  }

  if (Array.isArray(data)) {
    return (
      <div className="mb-4 p-3 border border-white/10 rounded-lg bg-black/20">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-bold text-green-400">{name} (Array)</span>
          <button onClick={() => onChange([...data, ""])} className="text-[10px] bg-primary/20 text-primary px-2 py-1 rounded flex items-center gap-1 hover:bg-primary/30">
            <Plus className="w-3 h-3" /> Add Item
          </button>
        </div>
        <div className="space-y-2 pl-2 border-l border-white/5">
          {data.map((item, idx) => (
            <div key={idx} className="flex items-start gap-2">
              <div className="flex-1">
                <RecursiveEditor 
                  name={`Item ${idx}`} 
                  data={item} 
                  onChange={(newVal) => {
                    const newArr = [...data];
                    newArr[idx] = newVal;
                    onChange(newArr);
                  }} 
                />
              </div>
              <button onClick={() => {
                const newArr = [...data];
                newArr.splice(idx, 1);
                onChange(newArr);
              }} className="text-red-400 hover:text-red-300 p-1 mt-1">
                <Trash2 className="w-3 h-3" />
              </button>
            </div>
          ))}
          {data.length === 0 && <span className="text-xs text-muted-foreground italic">Empty array</span>}
        </div>
      </div>
    );
  }

  if (typeof data === 'object') {
    return (
      <div className="mb-4 p-3 border border-white/10 rounded-lg bg-black/20">
        <span className="text-xs font-bold text-blue-400 block mb-2">{name} (Object)</span>
        <div className="space-y-1 pl-2 border-l border-white/5">
          {Object.entries(data).map(([key, val]) => (
            <RecursiveEditor 
              key={key} 
              name={key} 
              data={val} 
              onChange={(newVal) => {
                onChange({ ...data, [key]: newVal });
              }} 
            />
          ))}
          {Object.keys(data).length === 0 && <span className="text-xs text-muted-foreground italic">Empty object</span>}
        </div>
      </div>
    );
  }

  return <span className="text-xs text-red-400">Unsupported type for {name}</span>;
}
