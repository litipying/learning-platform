import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faPaperPlane } from '@fortawesome/free-solid-svg-icons';
import anime from 'animejs';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'alien';
  timestamp: Date;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: "Hi there! I'm Zorb from Planet Zorg. I'm excited to chat with you and help you learn English! What would you like to talk about?",
      sender: 'alien',
      timestamp: new Date()
    }
  ]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: messages.length + 1,
      text: newMessage,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');

    // Simulate alien typing
    setTimeout(() => {
      const alienMessage: Message = {
        id: messages.length + 2,
        text: "I'm sorry, but the chat feature is not implemented yet. Please check back later! 👽",
        sender: 'alien',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, alienMessage]);
    }, 1000);
  };

  const animateMessage = (element: Element) => {
    anime({
      targets: element,
      translateX: [20, 0],
      opacity: [0, 1],
      duration: 800,
      easing: 'easeOutElastic(1, .8)'
    });
  };

  useEffect(() => {
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node instanceof Element && node.classList.contains('message')) {
            animateMessage(node);
          }
        });
      });
    });

    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
      observer.observe(chatContainer, { childList: true, subtree: true });
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-300 via-amber-400 to-orange-400 p-6">
      {/* Navigation */}
      <div className="max-w-4xl mx-auto mb-8">
        <Link 
          to="/" 
          className="bg-gradient-to-br from-orange-300 to-yellow-300 p-3 rounded-full shadow-lg hover:scale-105 transition-transform inline-block"
        >
          <FontAwesomeIcon icon={faHome} className="text-xl text-white" />
        </Link>
      </div>

      {/* Chat Container */}
      <div className="max-w-4xl mx-auto">
        <div className="bg-white/20 backdrop-blur-lg rounded-3xl p-6 mb-6 h-[60vh] overflow-y-auto chat-container border-2 border-white/30 shadow-2xl">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`message flex ${
                message.sender === 'user' ? 'justify-end' : 'justify-start'
              } mb-4`}
            >
              <div
                className={`max-w-[80%] p-4 rounded-2xl shadow-lg ${
                  message.sender === 'user'
                    ? 'bg-gradient-to-r from-orange-400 to-yellow-400 text-white'
                    : 'bg-gradient-to-r from-yellow-300 to-amber-300 text-white'
                }`}
              >
                {message.sender === 'alien' && (
                  <div className="text-sm opacity-70 mb-1 flex items-center gap-2">
                    Zorb <span className="text-base">👽</span>
                  </div>
                )}
                <p className="text-lg">{message.text}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input */}
        <form onSubmit={handleSendMessage} className="flex gap-4">
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message..."
            className="flex-1 bg-white/20 backdrop-blur-lg rounded-2xl px-6 py-4 text-white placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-yellow-300 border-2 border-white/30 shadow-lg"
          />
          <button
            type="submit"
            className="bg-gradient-to-r from-orange-400 to-yellow-400 hover:from-orange-500 hover:to-yellow-500 text-white rounded-2xl px-8 py-4 transition-all hover:scale-105 shadow-lg"
          >
            <FontAwesomeIcon icon={faPaperPlane} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chat; 