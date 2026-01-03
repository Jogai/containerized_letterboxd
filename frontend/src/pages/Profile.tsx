import { useProfile } from '../hooks/useApi';

export default function Profile() {
  const { data: profile, loading } = useProfile();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-[#99aabb]">Loading profile...</div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="text-center py-12">
        <p className="text-[#99aabb]">No profile found</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-[#1c2228] rounded-lg p-6">
        <h1 className="text-2xl font-bold text-white">
          {profile.display_name || profile.username}
        </h1>
        <p className="text-[#99aabb]">@{profile.username}</p>

        {profile.bio && (
          <p className="text-[#ddd] mt-4">{profile.bio}</p>
        )}

        <div className="flex gap-6 mt-4 text-sm">
          {profile.location && (
            <span className="text-[#99aabb]">{profile.location}</span>
          )}
          {profile.website && (
            <a
              href={profile.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-[#00e054] hover:underline"
            >
              {profile.website.replace(/^https?:\/\//, '')}
            </a>
          )}
        </div>
      </div>

      {/* Stats */}
      {profile.stats && Object.keys(profile.stats).length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Letterboxd Stats</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {profile.stats.films !== undefined && (
              <div className="bg-[#1c2228] p-4 rounded-lg">
                <p className="text-2xl font-bold text-white">{profile.stats.films}</p>
                <p className="text-[#99aabb] text-sm">Films</p>
              </div>
            )}
            {profile.stats.this_year !== undefined && (
              <div className="bg-[#1c2228] p-4 rounded-lg">
                <p className="text-2xl font-bold text-white">{profile.stats.this_year}</p>
                <p className="text-[#99aabb] text-sm">This Year</p>
              </div>
            )}
            {profile.stats.lists !== undefined && (
              <div className="bg-[#1c2228] p-4 rounded-lg">
                <p className="text-2xl font-bold text-white">{profile.stats.lists}</p>
                <p className="text-[#99aabb] text-sm">Lists</p>
              </div>
            )}
            {profile.stats.following !== undefined && (
              <div className="bg-[#1c2228] p-4 rounded-lg">
                <p className="text-2xl font-bold text-white">{profile.stats.following}</p>
                <p className="text-[#99aabb] text-sm">Following</p>
              </div>
            )}
            {profile.stats.followers !== undefined && (
              <div className="bg-[#1c2228] p-4 rounded-lg">
                <p className="text-2xl font-bold text-white">{profile.stats.followers}</p>
                <p className="text-[#99aabb] text-sm">Followers</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Favorites */}
      {profile.favorites && profile.favorites.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-white mb-4">Favorite Films</h2>
          <div className="flex flex-wrap gap-2">
            {profile.favorites.map((slug: string) => (
              <span
                key={slug}
                className="px-3 py-1 bg-[#2c3440] text-[#99aabb] text-sm rounded"
              >
                {slug.replace(/-/g, ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Letterboxd link */}
      <div>
        <a
          href={`https://letterboxd.com/${profile.username}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-[#00e054] hover:underline"
        >
          View on Letterboxd &rarr;
        </a>
      </div>
    </div>
  );
}
