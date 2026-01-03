import { Link } from 'react-router-dom';
import { useReviews } from '../hooks/useApi';

export default function Reviews() {
  const { data: reviews, loading } = useReviews();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-pulse text-[#99aabb]">Loading reviews...</div>
      </div>
    );
  }

  if (reviews.length === 0) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold text-white mb-2">Reviews</h2>
        <p className="text-[#99aabb]">No reviews found</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white">Reviews</h2>
        <p className="text-[#99aabb]">{reviews.length} reviews</p>
      </div>

      <div className="space-y-6">
        {reviews.map((review) => (
          <div key={review.id} className="bg-[#1c2228] rounded-lg p-4 flex gap-4">
            {/* Poster */}
            <Link to={`/films/${review.film.id}`} className="flex-shrink-0">
              <div className="w-20 aspect-[2/3] bg-[#2c3440] rounded overflow-hidden">
                {review.film.poster_url ? (
                  <img
                    src={review.film.poster_url}
                    alt={review.film.title}
                    className="w-full h-full object-cover hover:scale-105 transition-transform"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-[#99aabb] text-xs text-center p-1">
                    {review.film.title}
                  </div>
                )}
              </div>
            </Link>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <Link
                    to={`/films/${review.film.id}`}
                    className="text-white font-semibold hover:text-[#00e054]"
                  >
                    {review.film.title}
                  </Link>
                  <span className="text-[#99aabb] ml-2">{review.film.year}</span>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {review.rating && (
                    <span className="text-[#00e054]">★ {review.rating}</span>
                  )}
                  {review.liked && <span className="text-[#ff8000]">♥</span>}
                </div>
              </div>

              <p className="text-[#99aabb] text-sm mt-1">
                {review.watched_date
                  ? new Date(review.watched_date).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                    })
                  : 'No date'}
              </p>

              <p className="text-[#ddd] mt-3 text-sm leading-relaxed whitespace-pre-wrap">
                {review.review_text}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
