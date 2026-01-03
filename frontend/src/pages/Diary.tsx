import { useDiary } from '../hooks/useApi';

export default function Diary() {
  const { data: entries, loading } = useDiary();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-[#99aabb]">Loading diary...</div>
      </div>
    );
  }

  // Group entries by month
  const groupedEntries: Record<string, typeof entries> = {};
  entries.forEach((entry) => {
    if (entry.watched_date) {
      const date = new Date(entry.watched_date);
      const monthKey = date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
      if (!groupedEntries[monthKey]) {
        groupedEntries[monthKey] = [];
      }
      groupedEntries[monthKey].push(entry);
    }
  });

  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold text-white">Diary</h2>
        <p className="text-[#99aabb]">{entries.length} entries</p>
      </div>

      {Object.entries(groupedEntries).map(([month, monthEntries]) => (
        <div key={month}>
          <h3 className="text-lg font-semibold text-white mb-4 border-b border-[#2c3440] pb-2">
            {month}
          </h3>
          <div className="space-y-3">
            {monthEntries.map((entry) => {
              const date = entry.watched_date ? new Date(entry.watched_date) : null;
              return (
                <div
                  key={entry.id}
                  className="flex items-center gap-4 p-3 bg-[#1c2228] rounded-lg hover:bg-[#2c3440] transition-colors"
                >
                  <div className="w-12 text-center">
                    <div className="text-2xl font-bold text-white">
                      {date?.getDate()}
                    </div>
                    <div className="text-xs text-[#99aabb] uppercase">
                      {date?.toLocaleDateString('en-US', { weekday: 'short' })}
                    </div>
                  </div>
                  <div className="w-12 h-18 flex-shrink-0">
                    {entry.film.poster_url ? (
                      <img
                        src={entry.film.poster_url}
                        alt={entry.film.title}
                        className="w-full h-full object-cover rounded"
                      />
                    ) : (
                      <div className="w-full h-full bg-[#2c3440] rounded" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">{entry.film.title}</p>
                    <p className="text-sm text-[#99aabb]">
                      {entry.film.year}
                      {entry.rewatch && ' • Rewatch'}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {entry.liked && (
                      <span className="text-[#ff8000]" title="Liked">
                        ♥
                      </span>
                    )}
                    {entry.rating && (
                      <span className="text-[#00e054] font-medium">
                        ★ {entry.rating}
                      </span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
