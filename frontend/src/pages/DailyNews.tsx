import React, { useEffect, useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { format } from 'date-fns';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome } from '@fortawesome/free-solid-svg-icons';

interface NewsArticle {
  id: number;
  alien_title: string;
  alien_content: string;
  video_path: string;
  created_at: string;
  vocab_words: Array<{
    word: string;
    explanation: string;
    sentence: string | null;
  }>;
}

const DailyNews: React.FC = () => {
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [currentArticleIndex, setCurrentArticleIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    fetchNews();
  }, []);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.load();
      videoRef.current.play().catch(error => {
        console.log('Video autoplay failed:', error);
      });
    }
  }, [currentArticleIndex]);

  const fetchNews = async () => {
    try {
      const response = await fetch('http://localhost:8003/news/');
      if (!response.ok) {
        throw new Error('Failed to fetch news');
      }
      const data = await response.json();
      setArticles(data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching news:', error);
      setLoading(false);
    }
  };

  const currentArticle = articles[currentArticleIndex];

  const goToNextArticle = () => {
    if (currentArticleIndex < articles.length - 1) {
      setCurrentArticleIndex(currentArticleIndex + 1);
    }
  };

  const goToPreviousArticle = () => {
    if (currentArticleIndex > 0) {
      setCurrentArticleIndex(currentArticleIndex - 1);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-400 via-purple-400 to-indigo-400 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="text-6xl mb-4 animate-bounce">👽</div>
          <div className="text-2xl font-bold">Loading alien news...</div>
        </div>
      </div>
    );
  }

  if (!currentArticle) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-400 via-purple-400 to-indigo-400 flex items-center justify-center">
        <div className="text-center text-white">
          <div className="text-6xl mb-4">🛸</div>
          <div className="text-2xl font-bold">No news from space today!</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-400 via-purple-400 to-indigo-400 overflow-hidden">
      <div className="max-w-4xl mx-auto p-4">
        {/* Header */}
        <div className="bg-white/20 backdrop-blur-lg rounded-3xl p-4 mb-6 flex items-center gap-4 shadow-2xl border-2 border-white/30">
          <Link 
            to="/" 
            className="bg-gradient-to-br from-pink-300 to-yellow-300 p-3 rounded-full shadow-lg hover:scale-105 transition-transform"
          >
            <FontAwesomeIcon icon={faHome} className="text-xl text-white" />
          </Link>
          <div className="flex-1 text-white">
            <h1 className="text-2xl font-bold whitespace-nowrap">Alien Daily News</h1>
            <p className="text-white/90">
              {format(new Date(currentArticle.created_at), 'MMMM d, yyyy')}
            </p>
          </div>
        </div>

        {/* Video Player */}
        <div className="bg-white/20 backdrop-blur-lg rounded-3xl p-6 mb-6 shadow-2xl border-2 border-white/30">
          <div className="aspect-video rounded-2xl overflow-hidden bg-black/30 mb-6">
            <video 
              ref={videoRef}
              src={currentArticle.video_path} 
              controls 
              className="w-full h-full"
            />
          </div>

          {/* Navigation Buttons */}
          <div className="flex justify-between gap-4">
            <button
              onClick={goToPreviousArticle}
              disabled={currentArticleIndex === 0}
              className={`flex-1 p-4 rounded-2xl font-bold text-white transition-all ${
                currentArticleIndex === 0
                ? 'bg-white/10 cursor-not-allowed'
                : 'bg-gradient-to-r from-pink-300 to-yellow-300 hover:scale-105'
              }`}
            >
              Previous News
            </button>
            <button
              onClick={goToNextArticle}
              disabled={currentArticleIndex === articles.length - 1}
              className={`flex-1 p-4 rounded-2xl font-bold text-white transition-all ${
                currentArticleIndex === articles.length - 1
                ? 'bg-white/10 cursor-not-allowed'
                : 'bg-gradient-to-r from-pink-300 to-yellow-300 hover:scale-105'
              }`}
            >
              Next News
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white/20 backdrop-blur-lg rounded-3xl p-6 mb-6 shadow-2xl border-2 border-white/30">
          <h2 className="text-2xl font-bold text-white mb-4">{currentArticle.alien_title}</h2>
          <p className="text-white/90 text-lg leading-relaxed whitespace-pre-line">
            {currentArticle.alien_content}
          </p>
        </div>

        {/* Vocabulary */}
        <div className="bg-white/20 backdrop-blur-lg rounded-3xl p-6 shadow-2xl border-2 border-white/30">
          <h3 className="text-2xl font-bold text-white mb-6">Today's Vocabulary</h3>
          <div className="grid gap-4">
            {currentArticle.vocab_words.map((item, index) => (
              <div 
                key={index}
                className="bg-gradient-to-r from-pink-300/10 to-yellow-300/10 rounded-2xl p-6 hover:from-pink-300/20 hover:to-yellow-300/20 transition-all"
              >
                <div className="text-xl font-bold text-white mb-2">{item.word}</div>
                <div className="text-white/90">{item.explanation}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DailyNews; 