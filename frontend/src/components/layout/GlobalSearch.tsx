import { useState, useEffect, useRef } from 'react';
import { Search, Loader2, FileText, Wifi, ShieldAlert } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useSearchStore } from '@/stores/searchStore';
import { cn } from '@/lib/cn';
import type { SearchResultItem } from '@/types/search';

export function GlobalSearch() {
  const [input, setInput] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const { results, isLoading, executeSearch, clearSearch } = useSearchStore();
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    if (!input.trim()) {
      clearSearch();
      return;
    }
    const timer = setTimeout(() => {
      executeSearch(input);
    }, 300);
    return () => clearTimeout(timer);
  }, [input, executeSearch, clearSearch]);

  const renderBadge = (type: string) => {
    switch (type) {
      case 'case':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-blue-500/10 text-blue-500 border border-blue-500/20 uppercase tracking-wide">
            Case
          </span>
        );
      case 'cdr_record':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 uppercase tracking-wide">
            CDR
          </span>
        );
      case 'tower':
        return (
          <span className="px-2 py-0.5 text-[10px] font-bold rounded-md bg-purple-500/10 text-purple-500 border border-purple-500/20 uppercase tracking-wide">
            Tower
          </span>
        );
      default:
        return null;
    }
  };

  const getLinkUrl = (item: SearchResultItem) => {
    switch (item.result_type) {
      case 'case':
        return `/cases/${item.id}`;
      case 'cdr_record':
        return item.case_id ? `/cases/${item.case_id}` : '/import';
      case 'tower':
        return '/investigation';
      default:
        return '#';
    }
  };

  const getItemIcon = (type: string) => {
    switch (type) {
      case 'case':
        return <FileText className="w-4.5 h-4.5 text-blue-500" />;
      case 'cdr_record':
        return <ShieldAlert className="w-4.5 h-4.5 text-emerald-500" />;
      case 'tower':
        return <Wifi className="w-4.5 h-4.5 text-purple-500" />;
      default:
        return null;
    }
  };

  const getItemDetails = (item: SearchResultItem) => {
    switch (item.result_type) {
      case 'case':
        return {
          title: item.title,
          subtitle: item.description || 'No description',
        };
      case 'cdr_record':
        return {
          title: item.target_number || item.imsi || `CDR Record #${item.id}`,
          subtitle: `${(item.operator || 'Unknown').toUpperCase()} | IMSI: ${item.imsi || '—'} | IMEI: ${item.imei || '—'}`,
        };
      case 'tower':
        return {
          title: item.tower_name,
          subtitle: `CGI: ${item.cgi || '—'} | Operator: ${(item.operator || 'unknown').toUpperCase()}`,
        };
    }
  };

  return (
    <div className="relative w-full max-w-md" ref={dropdownRef}>
      <div className="relative">
        <input
          type="text"
          value={input}
          onChange={(e) => {
            setInput(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder="Search IMSI, IMEI, Tower CGI, Case..."
          className={cn(
            'w-full pl-10 pr-10 py-2 bg-surface-secondary border border-border-primary rounded-xl text-sm transition-all focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary text-content-primary',
            isOpen && input.trim() && 'rounded-b-none'
          )}
        />
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-4 w-4 text-content-tertiary" />
        </div>
        {isLoading && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <Loader2 className="h-4 w-4 text-brand-primary animate-spin" />
          </div>
        )}
      </div>

      {isOpen && input.trim() && (
        <div className="absolute top-full left-0 right-0 bg-surface-primary border-x border-b border-border-primary rounded-b-xl shadow-lg z-50 max-h-96 overflow-y-auto divide-y divide-border-secondary">
          {results.length > 0 ? (
            results.map((item) => {
              const details = getItemDetails(item);
              return (
                <Link
                  key={`${item.result_type}-${item.id}`}
                  to={getLinkUrl(item)}
                  onClick={() => setIsOpen(false)}
                  className="flex items-center justify-between p-3 hover:bg-surface-secondary/50 transition-colors"
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <div className="p-1.5 bg-surface-secondary border border-border-secondary rounded-lg shrink-0">
                      {getItemIcon(item.result_type)}
                    </div>
                    <div className="min-w-0">
                      <div className="text-sm font-semibold text-content-primary truncate">
                        {details.title}
                      </div>
                      <div className="text-xs text-content-tertiary truncate">
                        {details.subtitle}
                      </div>
                    </div>
                  </div>
                  <div className="shrink-0 pl-2">
                    {renderBadge(item.result_type)}
                  </div>
                </Link>
              );
            })
          ) : (
            !isLoading && (
              <div className="p-4 text-center text-sm text-content-tertiary">
                No results found for "{input}"
              </div>
            )
          )}
        </div>
      )}
    </div>
  );
}
