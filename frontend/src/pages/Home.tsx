import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import anime from 'animejs';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faNewspaper, faComments } from '@fortawesome/free-solid-svg-icons';

const Home: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Create stars
    const createStars = () => {
      const container = document.querySelector('.mobile-container');
      const stars = [];
      for (let i = 0; i < 50; i++) {
        const star = document.createElement('div');
        star.className = 'star absolute bg-white rounded-full opacity-0';
        star.style.width = `${Math.random() * 3}px`;
        star.style.height = star.style.width;
        star.style.left = `${Math.random() * 100}%`;
        star.style.top = `${Math.random() * 100}%`;
        container?.appendChild(star);
        stars.push(star);
      }
      return stars;
    };

    const stars = createStars();

    // Animations
    anime({
      targets: '.planet-container',
      translateX: '-50%',
      scale: [0, 1],
      opacity: [0, 0.9],
      duration: 2000,
      easing: 'easeOutElastic(1, .5)',
      delay: 800
    });

    anime({
      targets: '.planet-body, .ring',
      rotate: '1turn',
      duration: 40000,
      loop: true,
      easing: 'linear'
    });

    anime({
      targets: '.ring',
      scaleY: [1, 0.85, 1],
      duration: 5000,
      loop: true,
      direction: 'alternate',
      easing: 'easeInOutQuad'
    });

    anime({
      targets: '.welcome-alien',
      translateY: [20, 0],
      opacity: [0, 1],
      duration: 1200,
      easing: 'easeOutElastic(1, .5)',
      delay: 300
    });

    anime({
      targets: '.welcome-text',
      translateY: [20, 0],
      opacity: [0, 1],
      duration: 800,
      easing: 'easeOutExpo',
      delay: 500
    });

    anime({
      targets: '.action-card',
      scale: [0.9, 1],
      opacity: [0, 1],
      duration: 1000,
      easing: 'easeOutElastic(1, .5)',
      delay: anime.stagger(200, {start: 800})
    });

    stars.forEach(star => {
      anime({
        targets: star,
        opacity: [0, 0.8],
        scale: [
          {value: [0, 1], duration: 400, easing: 'easeOutQuad'},
          {value: 0, duration: 400, delay: 400, easing: 'easeInQuad'}
        ],
        delay: anime.random(0, 2000),
        duration: 800,
        loop: true
      });
    });

    // Cleanup
    return () => {
      stars.forEach(star => star.remove());
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-400 via-blue-500 to-indigo-600 overflow-hidden">
      <div className="mobile-container relative max-w-4xl mx-auto p-4 pt-8">
        {/* Welcome Section */}
        <div className="bg-white/20 backdrop-blur-lg rounded-3xl p-8 mb-8 shadow-2xl border-2 border-white/30">
          <div className="flex items-center gap-4 mb-6">
            <div className="welcome-alien bg-gradient-to-br from-yellow-300 to-pink-300 p-4 rounded-full shadow-lg opacity-0">
              <span className="text-4xl">👽</span>
            </div>
            <div className="welcome-text opacity-0">
              <h1 className="text-white text-3xl font-bold mb-2">Hi Earthling!</h1>
              <p className="text-white/90 text-xl">Ready to learn English with aliens?</p>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 gap-6 mb-[300px]">
          <div 
            onClick={() => navigate('/news')}
            className="action-card bg-white/20 backdrop-blur-lg rounded-3xl p-8 text-white shadow-2xl border-2 border-white/30 opacity-0 hover:bg-white/30 transition-all cursor-pointer"
          >
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-br from-yellow-300 to-pink-300 p-4 rounded-full shadow-lg">
                <FontAwesomeIcon icon={faNewspaper} className="text-2xl text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold mb-2">Daily News</h3>
                <p className="text-white/90 text-lg">Learn new words from alien news!</p>
              </div>
            </div>
          </div>
          
          <div 
            onClick={() => navigate('/chat')}
            className="action-card bg-white/20 backdrop-blur-lg rounded-3xl p-8 text-white shadow-2xl border-2 border-white/30 opacity-0 hover:bg-white/30 transition-all cursor-pointer"
          >
            <div className="flex items-center gap-4">
              <div className="bg-gradient-to-br from-yellow-300 to-pink-300 p-4 rounded-full shadow-lg">
                <FontAwesomeIcon icon={faComments} className="text-2xl text-white" />
              </div>
              <div>
                <h3 className="text-2xl font-bold mb-2">Chat</h3>
                <p className="text-white/90 text-lg">Practice English with friendly aliens!</p>
              </div>
            </div>
          </div>
        </div>

        {/* Planet SVG */}
        <div className="planet-container fixed -bottom-[200px] left-1/2 w-[414px] max-w-full h-[414px] opacity-0 pointer-events-none -translate-x-1/2">
          <svg className="planet w-full h-full" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
            <defs>
              <linearGradient id="planetGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{ stopColor: '#FDE68A' }} /> {/* yellow-200 */}
                <stop offset="100%" style={{ stopColor: '#F472B6' }} /> {/* pink-400 */}
              </linearGradient>
              <linearGradient id="spotGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style={{ stopColor: '#FBCFE8' }} /> {/* pink-200 */}
                <stop offset="100%" style={{ stopColor: '#FCD34D' }} /> {/* yellow-400 */}
              </linearGradient>
            </defs>
            <circle cx="100" cy="100" r="65" fill="url(#planetGradient)" className="planet-body"/>
            <ellipse 
              cx="100" cy="100" rx="98" ry="28" 
              fill="none" 
              stroke="#F472B6" 
              strokeWidth="4" 
              className="ring ring-1"
              transform="rotate(15)"
              style={{ opacity: 0.6 }}
            /> {/* pink-400 */}
            <ellipse 
              cx="100" cy="100" rx="88" ry="23" 
              fill="none" 
              stroke="#FDE68A" 
              strokeWidth="3" 
              className="ring ring-2"
              transform="rotate(15)"
              style={{ opacity: 0.8 }}
            /> {/* yellow-200 */}
            <circle cx="75" cy="85" r="22" fill="url(#spotGradient)"/>
            <circle cx="120" cy="110" r="18" fill="url(#spotGradient)"/>
            <circle cx="90" cy="120" r="15" fill="url(#spotGradient)"/>
            <circle cx="110" cy="80" r="12" fill="url(#spotGradient)"/>
            <circle cx="85" cy="95" r="10" fill="url(#spotGradient)"/>
          </svg>
        </div>
      </div>
    </div>
  );
};

export default Home; 