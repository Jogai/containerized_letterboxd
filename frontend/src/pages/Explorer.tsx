import { useState } from 'react';
import { Select, SelectItem, TextInput } from '@tremor/react';
import { useExplorer } from '../hooks/useApi';

function formatCurrency(num: number | null | undefined): string {
  if (!num) return '-';
  if (num >= 1_000_000_000) return `$${(num / 1_000_000_000).toFixed(1)}B`;
  if (num >= 1_000_000) return `$${(num / 1_000_000).toFixed(0)}M`;
  if (num >= 1_000) return `$${(num / 1_000).toFixed(0)}K`;
  return `$${num}`;
}

function FilmRow({ film, isExpanded, onToggle }: { film: any; isExpanded: boolean; onToggle: () => void }) {
  const tmdb = film.tmdb;
  const lb = film.letterboxd;
  const user = film.user;

  return (
    <div className="border border-[#456] rounded-lg overflow-hidden bg-[#1a1f25]">
      {/* Summary Row */}
      <div
        className="flex items-center gap-4 p-3 cursor-pointer hover:bg-[#2c3440] transition-colors"
        onClick={onToggle}
      >
        {/* Poster */}
        <div className="w-12 h-18 flex-shrink-0">
          {film.poster_url ? (
            <img src={film.poster_url} alt={film.title} className="w-full h-full object-cover rounded" />
          ) : (
            <div className="w-full h-full bg-[#2c3440] rounded flex items-center justify-center text-[10px] text-[#99aabb]">
              No img
            </div>
          )}
        </div>

        {/* Title & Year */}
        <div className="flex-1 min-w-0">
          <h3 className="text-white font-medium truncate">{film.title}</h3>
          <p className="text-sm text-[#99aabb]">{film.year}</p>
        </div>

        {/* Ratings */}
        <div className="flex gap-4 text-sm">
          <div className="text-center">
            <div className="text-[#00e054] font-medium">{user.rating ? `★ ${user.rating}` : '-'}</div>
            <div className="text-[10px] text-[#99aabb]">You</div>
          </div>
          <div className="text-center">
            <div className="text-[#40bcf4] font-medium">{lb.rating ? lb.rating.toFixed(1) : '-'}</div>
            <div className="text-[10px] text-[#99aabb]">LB</div>
          </div>
          <div className="text-center">
            <div className="text-[#f5c518] font-medium">{tmdb?.vote_average ? tmdb.vote_average.toFixed(1) : '-'}</div>
            <div className="text-[10px] text-[#99aabb]">TMDB</div>
          </div>
        </div>

        {/* Certification */}
        <div className="w-12 text-center">
          {tmdb?.certification && (
            <span className="px-2 py-0.5 bg-[#456] text-white text-xs rounded">{tmdb.certification}</span>
          )}
        </div>

        {/* Budget */}
        <div className="w-20 text-right text-sm text-[#99aabb]">
          {formatCurrency(tmdb?.budget)}
        </div>

        {/* Expand Toggle */}
        <div className="w-8 text-center text-[#99aabb]">
          {isExpanded ? '−' : '+'}
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-[#456] p-4 bg-[#14181c]">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Letterboxd Data */}
            <div>
              <h4 className="text-[#40bcf4] font-medium mb-3 text-sm uppercase tracking-wide">Letterboxd</h4>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-[#99aabb]">Rating</span>
                  <span className="text-white">{lb.rating ? `${lb.rating.toFixed(2)} (${lb.rating_count?.toLocaleString() || '?'} votes)` : '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#99aabb]">Runtime</span>
                  <span className="text-white">{lb.runtime_minutes ? `${lb.runtime_minutes} min` : '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#99aabb]">Directors</span>
                  <span className="text-white truncate ml-4">{lb.directors?.map((d: any) => d.name).join(', ') || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#99aabb]">Genres</span>
                  <span className="text-white truncate ml-4">{lb.genres?.map((g: any) => g.name).join(', ') || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#99aabb]">Countries</span>
                  <span className="text-white truncate ml-4">{lb.countries?.map((c: any) => c.name).join(', ') || '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#99aabb]">Studios</span>
                  <span className="text-white truncate ml-4">{lb.studios?.map((s: any) => s.name).join(', ') || '-'}</span>
                </div>
                {lb.tagline && (
                  <div className="pt-2">
                    <span className="text-[#99aabb]">Tagline</span>
                    <p className="text-white italic mt-1">"{lb.tagline}"</p>
                  </div>
                )}
                {lb.url && (
                  <a href={lb.url} target="_blank" rel="noopener noreferrer" className="text-[#40bcf4] hover:underline block mt-2">
                    View on Letterboxd →
                  </a>
                )}
              </div>
            </div>

            {/* TMDB Data */}
            <div>
              <h4 className="text-[#f5c518] font-medium mb-3 text-sm uppercase tracking-wide">TMDB</h4>
              {tmdb ? (
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-[#99aabb]">Rating</span>
                    <span className="text-white">{tmdb.vote_average ? `${tmdb.vote_average.toFixed(1)}/10 (${tmdb.vote_count?.toLocaleString()} votes)` : '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#99aabb]">Budget</span>
                    <span className="text-white">{tmdb.budget ? `$${tmdb.budget.toLocaleString()}` : '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#99aabb]">Revenue</span>
                    <span className="text-white">{tmdb.revenue ? `$${tmdb.revenue.toLocaleString()}` : '-'}</span>
                  </div>
                  {tmdb.budget && tmdb.revenue && (
                    <div className="flex justify-between">
                      <span className="text-[#99aabb]">ROI</span>
                      <span className={tmdb.revenue > tmdb.budget ? 'text-[#00e054]' : 'text-[#ff6666]'}>
                        {((tmdb.revenue / tmdb.budget - 1) * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-[#99aabb]">Certification</span>
                    <span className="text-white">{tmdb.certification || '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#99aabb]">Release Date</span>
                    <span className="text-white">{tmdb.release_date || '-'}</span>
                  </div>
                  {tmdb.collection && (
                    <div className="flex justify-between">
                      <span className="text-[#99aabb]">Collection</span>
                      <span className="text-white">{tmdb.collection.name}</span>
                    </div>
                  )}
                  {tmdb.keywords && tmdb.keywords.length > 0 && (
                    <div className="pt-2">
                      <span className="text-[#99aabb]">Keywords</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {tmdb.keywords.slice(0, 10).map((kw: any) => (
                          <span key={kw.id} className="px-2 py-0.5 bg-[#2c3440] text-[#99aabb] text-xs rounded">
                            {kw.name}
                          </span>
                        ))}
                        {tmdb.keywords.length > 10 && (
                          <span className="text-[#99aabb] text-xs">+{tmdb.keywords.length - 10} more</span>
                        )}
                      </div>
                    </div>
                  )}
                  {tmdb.watch_providers?.US?.flatrate && tmdb.watch_providers.US.flatrate.length > 0 && (
                    <div className="pt-2">
                      <span className="text-[#99aabb]">Streaming (US)</span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {tmdb.watch_providers.US.flatrate.map((p: any) => (
                          <span key={p.id} className="px-2 py-0.5 bg-[#00e054] text-black text-xs rounded font-medium">
                            {p.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-[#99aabb] italic">No TMDB data available</p>
              )}
            </div>
          </div>

          {/* User Data */}
          <div className="mt-4 pt-4 border-t border-[#456]">
            <h4 className="text-[#00e054] font-medium mb-3 text-sm uppercase tracking-wide">Your Activity</h4>
            <div className="flex gap-6 text-sm">
              <div>
                <span className="text-[#99aabb]">Rating: </span>
                <span className="text-white">{user.rating ? `★ ${user.rating}` : 'Not rated'}</span>
              </div>
              <div>
                <span className="text-[#99aabb]">Watches: </span>
                <span className="text-white">{user.watch_count}</span>
              </div>
              {user.first_watched && (
                <div>
                  <span className="text-[#99aabb]">First watched: </span>
                  <span className="text-white">{new Date(user.first_watched).toLocaleDateString()}</span>
                </div>
              )}
              {user.liked && <span className="text-[#ff8000]">♥ Liked</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function Explorer() {
  const [sort, setSort] = useState('title');
  const [order, setOrder] = useState('asc');
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(1);
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  const { data, loading } = useExplorer(sort, order, search, page);

  const toggleExpanded = (id: number) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearch(searchInput);
    setPage(1);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-[#99aabb]">Loading data...</div>
      </div>
    );
  }

  const films = data?.films || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white">Data Explorer</h2>
        <p className="text-[#99aabb]">
          Browse all your film data from Letterboxd + TMDB
        </p>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap gap-4 items-center">
        <form onSubmit={handleSearch} className="flex gap-2">
          <TextInput
            placeholder="Search films..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-64"
          />
          <button
            type="submit"
            className="px-4 py-2 bg-[#00e054] text-black rounded font-medium hover:bg-[#00c049] transition-colors"
          >
            Search
          </button>
        </form>

        <Select value={sort} onValueChange={(v) => { setSort(v); setPage(1); }} className="w-40">
          <SelectItem value="title">Sort: Title</SelectItem>
          <SelectItem value="year">Sort: Year</SelectItem>
          <SelectItem value="rating">Sort: Your Rating</SelectItem>
          <SelectItem value="budget">Sort: Budget</SelectItem>
          <SelectItem value="revenue">Sort: Revenue</SelectItem>
          <SelectItem value="tmdb_rating">Sort: TMDB Rating</SelectItem>
        </Select>

        <Select value={order} onValueChange={(v) => { setOrder(v); setPage(1); }} className="w-36">
          <SelectItem value="asc">Ascending</SelectItem>
          <SelectItem value="desc">Descending</SelectItem>
        </Select>

        <span className="text-[#99aabb] text-sm ml-auto">
          {data?.count || 0} films (page {data?.page || 1} of {data?.total_pages || 1})
        </span>
      </div>

      {/* Film List */}
      <div className="space-y-2">
        {films.map((film: any) => (
          <FilmRow
            key={film.id}
            film={film}
            isExpanded={expandedIds.has(film.id)}
            onToggle={() => toggleExpanded(film.id)}
          />
        ))}
      </div>

      {films.length === 0 && (
        <div className="text-center py-12 text-[#99aabb]">
          No films found
        </div>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-4">
          <button
            onClick={() => setPage(1)}
            disabled={page === 1}
            className="px-3 py-1 rounded bg-[#2c3440] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#3c4450] transition-colors"
          >
            First
          </button>
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 rounded bg-[#2c3440] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#3c4450] transition-colors"
          >
            Prev
          </button>
          <span className="px-4 text-[#99aabb]">
            Page {page} of {data.total_pages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(data.total_pages, p + 1))}
            disabled={page === data.total_pages}
            className="px-3 py-1 rounded bg-[#2c3440] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#3c4450] transition-colors"
          >
            Next
          </button>
          <button
            onClick={() => setPage(data.total_pages)}
            disabled={page === data.total_pages}
            className="px-3 py-1 rounded bg-[#2c3440] text-white disabled:opacity-50 disabled:cursor-not-allowed hover:bg-[#3c4450] transition-colors"
          >
            Last
          </button>
        </div>
      )}
    </div>
  );
}
