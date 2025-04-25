import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faHome, faPaperPlane, faPlay, faArrowRight, faMicrophone, faStop } from '@fortawesome/free-solid-svg-icons';
import anime from 'animejs';
import axios from 'axios';

// Add CSS for message highlight effect
const highlightStyles = `
  .message-highlight {
    box-shadow: 0 0 15px rgba(255, 255, 255, 0.8);
    transform: scale(1.02);
    border: 2px solid white;
  }
`;

// Environment variables for API keys
const ELEVENLABS_API_KEY = import.meta.env.VITE_ELEVENLABS_API_KEY || '';
const GEMINI_API_KEY = import.meta.env.VITE_GEMINI_API_KEY || '';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'alien';
  timestamp: Date;
}

interface Scene {
  id: number;
  story_id: number;
  scene_number: number;
  description: string;
  scene_story?: string;
  image_path: string;
  audio_path: string;
  image_url: string;
  audio_url: string;
}

interface StoryCharacter {
  story_id: number;
  title: string;
  character_name: string;
  character_image_path: string;
  moral: string;
  scene_count: number;
  date: string;
  voice_id?: string; // Optional voice_id for character responses
}

interface StoryData {
  date: string;
  stories: StoryCharacter[];
  scenes: Scene[];
}

// API URL
const API_URL = 'http://localhost:8003';

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Story playback state
  const [showStoryPlayback, setShowStoryPlayback] = useState(true);
  const [storyData, setStoryData] = useState<StoryData | null>(null);
  const [currentScene, setCurrentScene] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [isAudioFinished, setIsAudioFinished] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement>(null);

  // Voice chat state
  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [recordingStatus, setRecordingStatus] = useState<string>('');
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Voice output state
  const [isPlayingResponse, setIsPlayingResponse] = useState<boolean>(false);
  const characterAudioRef = useRef<HTMLAudioElement | null>(null);

  // Fetch the latest story on component mount
  useEffect(() => {
    const fetchLatestStory = async () => {
      try {
        // First get the available dates
        const datesResponse = await axios.get(`${API_URL}/story/dates`);
        const dates = datesResponse.data;
        
        if (dates && dates.length > 0) {
          // Get the latest date
          const latestDate = dates[0];
          
          // Fetch the story for that date
          const storyResponse = await axios.get(`${API_URL}/story/scenes/date/${latestDate}?latest_only=true`);
          setStoryData(storyResponse.data);
        } else {
          setError("No stories available");
        }
      } catch (err) {
        console.error("Error fetching story:", err);
        setError("Error loading story");
      }
    };

    fetchLatestStory();
  }, []);

  // Create welcome message when story data is loaded or when transitioning to chat
  useEffect(() => {
    if (!showStoryPlayback && storyData) {
      // Generate a welcome message based on character and story
      const character = storyData.stories[0];
      const welcomeMessage = createWelcomeMessage(character);
      
      setMessages([
        {
          id: 1,
          text: welcomeMessage,
          sender: 'alien',
          timestamp: new Date()
        }
      ]);
    }
  }, [showStoryPlayback, storyData]);

  // Function to create a personalized welcome message
  const createWelcomeMessage = (character: StoryCharacter): string => {
    if (!character) {
      return "Hi there! I'm an alien friend here to chat with you. What would you like to talk about?";
    }

    // Extract story title and character name
    const characterName = character.character_name;
    const storyTitle = character.title;
    
    // Get story context if available
    let storyContext = "";
    const sceneOne = findSceneData(1);
    
    if (sceneOne) {
      // Extract some keywords from the first scene description
      const description = sceneOne.description || "";
      
      // Get location or key elements from the description
      const locationMatch = description.match(/(?:in|at|on) (?:the|a) ([^,.!?]+)/i);
      const location = locationMatch ? locationMatch[1].trim() : "";
      
      if (location) {
        storyContext = ` I'm still thinking about my adventure in ${location}!`;
      }
    }
    
    // Include moral lesson if available
    let moralLesson = "";
    if (character.moral) {
      moralLesson = ` I learned that "${character.moral.split('.')[0]}."`;
    }
    
    // Generate a welcome message based on the character and story
    return `Hi there! I'm ${characterName} from the story "${storyTitle}".${storyContext}${moralLesson} I'd love to chat with you about my adventure or anything else you'd like to know. What's on your mind?`;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Initialize MediaRecorder for voice input
  const initializeMediaRecorder = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      mediaRecorder.onstart = () => {
        audioChunksRef.current = [];
        setRecordingStatus('Recording...');
      };
      
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        setRecordingStatus('Processing...');
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        
        // Call the function to convert speech to text
        await convertSpeechToText(audioBlob);
      };
      
      mediaRecorderRef.current = mediaRecorder;
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setRecordingStatus('Microphone access denied');
    }
  };

  // Start/stop voice recording
  const toggleRecording = async () => {
    // Don't allow recording while response is playing
    if (isPlayingResponse) {
      return;
    }
    
    if (!isRecording) {
      // Initialize if needed
      if (!mediaRecorderRef.current) {
        await initializeMediaRecorder();
      }
      
      // Start recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'inactive') {
        mediaRecorderRef.current.start();
        setIsRecording(true);
      }
    } else {
      // Stop recording
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
        setIsRecording(false);
      }
    }
  };

  // Convert speech to text using ElevenLabs API
  const convertSpeechToText = async (audioBlob: Blob) => {
    try {
      // Create form data to send to ElevenLabs
      const formData = new FormData();
      formData.append('model_id', 'scribe_v1'); // Use scribe_v1 model
      formData.append('file', audioBlob);
      
      // Make request to ElevenLabs Speech-to-Text API
      const response = await axios.post(
        'https://api.elevenlabs.io/v1/speech-to-text',
        formData,
        {
          headers: {
            'xi-api-key': ELEVENLABS_API_KEY,
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      
      // Extract transcribed text
      const transcribedText = response.data.text;
      setRecordingStatus('');
      
      if (transcribedText && transcribedText.trim() !== '') {
        // Update input field with transcribed text
        setNewMessage(transcribedText);
        
        // Automatically send the message
        await sendMessage(transcribedText);
      } else {
        setRecordingStatus('No speech detected');
        setTimeout(() => setRecordingStatus(''), 2000);
      }
    } catch (err) {
      console.error('Error converting speech to text:', err);
      setRecordingStatus('Error processing speech');
      setTimeout(() => setRecordingStatus(''), 2000);
    }
  };

  // Generate responses that incorporate character personality and story elements
  const generateCharacterResponse = async (userMessage: string): Promise<string> => {
    if (!storyData || !storyData.stories[0]) {
      return "I'm sorry, but the chat feature is not fully implemented yet. Please check back later! 👽";
    }
    
    const character = storyData.stories[0];
    const characterName = character.character_name;
    
    if (!GEMINI_API_KEY) {
      console.warn("Gemini API key not found, using fallback response generation");
      // Fallback to simple keyword response system if no API key
      
      // Simple keyword-based responses
      const lowerCaseMessage = userMessage.toLowerCase();
      
      if (lowerCaseMessage.includes("hello") || lowerCaseMessage.includes("hi")) {
        return `Hello there! It's great to meet you. I'm ${characterName} and I'm excited to chat with you!`;
      }
      
      if (lowerCaseMessage.includes("story") || lowerCaseMessage.includes("adventure")) {
        return `My adventure was quite exciting! I learned a lot during my journey. Is there a specific part of my story you'd like to talk about?`;
      }
      
      if (lowerCaseMessage.includes("favorite") || lowerCaseMessage.includes("like")) {
        return `As an adventurer, I enjoy making new friends and exploring new places! What do you like to do?`;
      }
      
      if (lowerCaseMessage.includes("who") && lowerCaseMessage.includes("you")) {
        return `I'm ${characterName}, the main character from the story you just experienced! I've been on quite a journey and I'm happy to share more about it.`;
      }
      
      // Default response
      return `That's an interesting thought! As ${characterName}, I'm still learning about your world. Would you like to tell me more?`;
    }
    
    try {
      // Create prompt with character info, story context and conversation history
      const prompt = createGeminiPrompt(userMessage);

      console.log("Prompt:", prompt);
      
      // Call Gemini API
      const response = await callGeminiAPI(prompt);
      return response;
    } catch (error) {
      console.error("Error calling Gemini API:", error);
      return `I'm ${characterName} and I'd love to respond, but I'm having trouble connecting to my thought processor right now. Could you try again in a moment?`;
    }
  };

  // Create a prompt for Gemini that includes character info, story context and conversation history
  const createGeminiPrompt = (currentUserMessage: string): string => {
    const character = storyData?.stories[0];
    if (!character) return "";
    
    // Get basic character and story information
    const characterInfo = `
Character Name: ${character.character_name}
Story Title: ${character.title}
Moral of the Story: ${character.moral || "None specified"}
    `;
    
    // Get scene information for context
    let sceneContext = "";
    storyData?.scenes.forEach((scene, index) => {
      sceneContext += `Scene ${index + 1}: ${scene.description}\n`;
    });
    
    // Get conversation history (last 20 messages or less)
    const recentMessages = messages.slice(-20);
    let conversationHistory = "";
    recentMessages.forEach(msg => {
      const role = msg.sender === 'user' ? 'Human' : character.character_name;
      conversationHistory += `${role}: ${msg.text}\n`;
    });
    
    // Add current user message
    conversationHistory += `Human: ${currentUserMessage}\n`;
    
    // Construct the final prompt with clear instructions
    const finalPrompt = `
You are roleplaying as ${character.character_name} from the story titled "${character.title}".

CHARACTER INFORMATION:
${characterInfo}

STORY CONTEXT:
${sceneContext}

CONVERSATION HISTORY:
${conversationHistory}

${character.character_name}:

INSTRUCTIONS:
1. Respond as ${character.character_name}, maintaining their personality and perspective.
2. Reference events and details from the story when relevant.
3. Keep responses friendly, engaging, and suitable for all ages.
4. Responses should be 1-3 sentences long unless the user asks for more detail.
5. Never break character or mention that you are an AI.
6. If asked about things outside the story context, respond with curiosity and relate it back to your experiences.
7. Include references to the moral of the story when appropriate.
`;

    return finalPrompt;
  };

  // Function to call Gemini API
  const callGeminiAPI = async (prompt: string): Promise<string> => {
    try {
      const response = await axios.post(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent',
        {
          contents: [
            {
              parts: [
                {
                  text: prompt
                }
              ]
            }
          ],
          generationConfig: {
            temperature: 0.7,
            topK: 40,
            topP: 0.95,
            maxOutputTokens: 300,
          }
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'x-goog-api-key': GEMINI_API_KEY
          }
        }
      );
      
      // Extract the response text
      if (response.data?.candidates?.[0]?.content?.parts?.[0]?.text) {
        return response.data.candidates[0].content.parts[0].text;
      }
      
      throw new Error('Unexpected response format from Gemini API');
    } catch (error) {
      console.error('Error calling Gemini API:', error);
      throw error;
    }
  };

  // Generate AI response audio using ElevenLabs API
  const generateResponseAudio = async (text: string): Promise<string> => {
    if (!ELEVENLABS_API_KEY || !storyData?.stories[0]) {
      console.warn("ElevenLabs API key not found or story data missing");
      return '';
    }
    
    try {
      // Use the voice_id from the story if available
      const voiceId = storyData.stories[0].voice_id || 'Guz7MJEhTfoBz61JbQyO'; // Default voice ID as fallback
      
      // Call ElevenLabs API to generate speech
      const response = await axios.post(
        `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
        {
          text: text,
          model_id: "eleven_multilingual_v2",
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.75
          }
        },
        {
          headers: {
            'xi-api-key': ELEVENLABS_API_KEY,
            'Content-Type': 'application/json',
            'Accept': 'audio/mpeg'
          },
          responseType: 'blob'
        }
      );
      
      // Create a URL for the audio blob
      const audioUrl = URL.createObjectURL(response.data);
      return audioUrl;
    } catch (error) {
      console.error('Error generating speech:', error);
      return '';
    }
  };

  // Play audio for character response
  const playResponseAudio = (audioUrl: string, responseText: string) => {
    if (!audioUrl) {
      console.log("No audio URL provided for playback");
      return;
    }
    
    // Create audio element if it doesn't exist
    if (!characterAudioRef.current) {
      characterAudioRef.current = new Audio();
      
      // Set up event listeners
      characterAudioRef.current.onended = () => {
        console.log("Character response audio finished");
        setIsPlayingResponse(false);
        
        // Remove highlight when audio finishes
        const alienMessage = document.querySelector('.message-highlight');
        if (alienMessage) {
          alienMessage.classList.remove('message-highlight');
        }
      };
      
      characterAudioRef.current.onerror = (e) => {
        console.error("Error playing character response audio:", e);
        setIsPlayingResponse(false);
        
        // Remove highlight on error
        const alienMessage = document.querySelector('.message-highlight');
        if (alienMessage) {
          alienMessage.classList.remove('message-highlight');
        }
      };
    }
    
    // Set the source and play
    characterAudioRef.current.src = audioUrl;
    characterAudioRef.current.play()
      .then(() => {
        console.log("Playing character response audio");
        setIsPlayingResponse(true);
        
        // Add highlight to the most recent alien message
        const alienMessages = document.querySelectorAll('.alien-message');
        if (alienMessages.length > 0) {
          const lastAlienMessage = alienMessages[alienMessages.length - 1];
          lastAlienMessage.classList.add('message-highlight');
        }
      })
      .catch(err => {
        console.error("Failed to play character response audio:", err);
        setIsPlayingResponse(false);
      });
  };

  // Send message (can be called from text input or voice)
  const sendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;
    
    // Add user message
    const userMessage: Message = {
      id: messages.length + 1,
      text: messageText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setNewMessage('');

    // Show typing indicator or loading state
    setMessages(prev => [...prev, {
      id: -1, // Temporary ID for loading indicator
      text: "...",
      sender: 'alien',
      timestamp: new Date()
    }]);

    try {
      // Generate a character-based response using Gemini
      const responseText = await generateCharacterResponse(messageText);
      
      // Generate audio for the response in parallel
      const audioPromise = generateResponseAudio(responseText);
      
      // Remove the loading indicator
      setMessages(prev => prev.filter(msg => msg.id !== -1));
      
      // Add the real response immediately
      const alienMessage: Message = {
        id: messages.length + 2,
        text: responseText,
        sender: 'alien',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, alienMessage]);
      
      // Wait for audio generation to complete and play it
      const audioUrl = await audioPromise;
      if (audioUrl) {
        playResponseAudio(audioUrl, responseText);
      }
    } catch (error) {
      // Remove the loading indicator
      setMessages(prev => prev.filter(msg => msg.id !== -1));
      
      // Add an error message
      const errorMessage: Message = {
        id: messages.length + 2,
        text: "Sorry, I'm having trouble connecting right now. Can we try again?",
        sender: 'alien',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
      console.error("Error generating response:", error);
    }
  };
  
  // Handle form submission for text input
  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(newMessage);
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

  // Story playback functionality
  const startStoryPlayback = () => {
    setCurrentScene(1);
    setIsAudioFinished(false); // Reset audio state
    // Note: We'll let the audio element handle playback via the source tag
  };

  const goToNextScene = () => {
    if (currentScene < 4) {
      setCurrentScene(currentScene + 1);
      setIsAudioFinished(false);
      // Audio playback will be handled by the audio element when scene changes
    } else {
      // Finished all scenes, show chat interface
      setShowStoryPlayback(false);
    }
  };

  // Find the correct scene data for the current scene number
  const findSceneData = (sceneNumber: number): Scene | null => {
    if (!storyData) return null;

    // First, try to find by scene_number
    const sceneByNumber = storyData.scenes.find(s => s.scene_number === sceneNumber);
    if (sceneByNumber) {
      console.log(`Found scene ${sceneNumber} by scene_number:`, sceneByNumber);
      return sceneByNumber;
    }

    // If that fails, try to get scenes for the current story and order by scene_number
    const storyId = storyData.stories[0]?.story_id;
    if (storyId) {
      // Get all scenes for this story
      const storyScenes = storyData.scenes
        .filter(s => s.story_id === storyId)
        .sort((a, b) => (a.scene_number || 0) - (b.scene_number || 0));

      // Try to get by index (0-based index, so we subtract 1 from scene number)
      if (storyScenes.length >= sceneNumber && sceneNumber > 0) {
        const sceneByIndex = storyScenes[sceneNumber - 1];
        console.log(`Found scene ${sceneNumber} by index:`, sceneByIndex);
        return sceneByIndex;
      }
    }

    console.error(`No scene found for scene number ${sceneNumber}`);
    return null;
  };

  // Effect to play audio when scene changes
  useEffect(() => {
    if (currentScene > 0) {
      console.log("Current scene changed to:", currentScene);
      
      const sceneData = findSceneData(currentScene);
      if (sceneData) {
        playAudioForScene(sceneData);
      } else {
        // No scene data found, allow proceeding anyway
        setIsAudioFinished(true);
      }
    }
  }, [currentScene, storyData]);
  
  // Function to play audio for a specific scene
  const playAudioForScene = (sceneData: Scene) => {
    if (audioRef.current && sceneData.audio_url) {
      console.log(`Playing audio for scene ${sceneData.scene_number}:`, sceneData.audio_url);
      
      // Ensure we have a valid audio URL
      let audioUrl = sceneData.audio_url;
      
      // If the URL is relative, make it absolute with the API_URL
      if (!audioUrl.startsWith('http')) {
        audioUrl = `${API_URL}${audioUrl}`;
      }
      
      console.log("Final audio URL:", audioUrl);
      
      // Set the source and load the audio
      audioRef.current.src = audioUrl;
      audioRef.current.load(); // Explicitly load before playing
      
      // Add a small delay to ensure audio element is ready
      setTimeout(() => {
        if (audioRef.current) {
          // Play with error handling
          const playPromise = audioRef.current.play();
          if (playPromise !== undefined) {
            playPromise
              .then(() => {
                console.log("Audio playing successfully");
                setIsPlaying(true);
                
                // Auto-scroll the scene narration to the top when audio starts
                const narrationContainer = document.querySelector('.scene-narration');
                if (narrationContainer) {
                  narrationContainer.scrollTop = 0;
                  console.log("Scrolled narration container to top");
                } else {
                  console.log("Could not find narration container to scroll");
                }
              })
              .catch(err => {
                console.error('Error playing audio:', err);
                console.error('Audio element state:', {
                  src: audioRef.current?.src,
                  paused: audioRef.current?.paused,
                  readyState: audioRef.current?.readyState,
                  error: audioRef.current?.error
                });
                setIsAudioFinished(true); // Allow proceed even if audio fails
              });
          }
        }
      }, 300);
    } else {
      console.log("No audio URL found or audio ref not available");
      setIsAudioFinished(true);
    }
  };

  // Render Story Playback View
  const renderStoryPlayback = () => {
    if (!storyData && !error) {
      return (
        <div className="flex flex-col items-center justify-center h-full">
          <div className="text-white text-xl">Loading story...</div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center h-full">
          <div className="text-white text-xl">{error}</div>
          <button 
            onClick={() => setShowStoryPlayback(false)}
            className="mt-4 bg-gradient-to-r from-orange-400 to-yellow-400 text-white px-6 py-3 rounded-full hover:scale-105 transition-transform"
          >
            Go to Chat
          </button>
        </div>
      );
    }

    if (currentScene === 0) {
      // Show start screen
      return (
        <div className="flex flex-col items-center justify-center h-full p-6 text-center">
          <h2 className="text-2xl font-bold text-white mb-4">
            {storyData?.stories[0]?.title || "Adventure Story"}
          </h2>
          <p className="text-white mb-8">Join {storyData?.stories[0]?.character_name || "our character"} on an exciting adventure!</p>
          
          {storyData?.stories[0]?.character_image_path && (
            <div className="mb-8 w-48 h-48 rounded-full overflow-hidden border-4 border-white shadow-lg">
              <img 
                src={storyData.stories[0].character_image_path} 
                alt={storyData.stories[0].character_name}
                className="w-full h-full object-cover" 
              />
            </div>
          )}
          
          <button
            onClick={startStoryPlayback}
            className="bg-gradient-to-r from-orange-400 to-yellow-400 text-white text-xl px-8 py-4 rounded-full hover:scale-105 transition-transform flex items-center gap-2"
          >
            <FontAwesomeIcon icon={faPlay} /> Start Story
          </button>
        </div>
      );
    }

    // Show scene playback
    const currentSceneData = findSceneData(currentScene);
    console.log("Rendering scene playback for scene:", currentScene, "Data:", currentSceneData);
    
    return (
      <div className="flex flex-col h-full p-4">
        {/* Scene image */}
        {currentSceneData?.image_url ? (
          <div className="mb-4 flex-1 relative rounded-2xl overflow-hidden border-2 border-white/30 shadow-lg">
            <img 
              src={currentSceneData.image_url.startsWith('http') ? 
                currentSceneData.image_url :
                `${API_URL}${currentSceneData.image_url}`} 
              alt={`Scene ${currentScene}`}
              className="w-full h-full object-cover" 
            />
          </div>
        ) : (
          <div className="mb-4 flex-1 flex items-center justify-center bg-gray-700/30 rounded-2xl">
            <p className="text-white">Image not available</p>
          </div>
        )}
        
        {/* Scene description and narration */}
        <div className="space-y-4 mb-4">
          {/* Scene narration (for audio) */}
          {currentSceneData?.scene_story && (
            <div className="scene-narration bg-white/20 backdrop-blur-md rounded-xl p-4 shadow-lg border border-white/30 h-28 overflow-auto">
              <p className="text-white italic">{currentSceneData.scene_story}</p>
            </div>
          )}
          
          {/* Scene description (visual details) */}
          {/* <div className="bg-white/20 backdrop-blur-md rounded-xl p-4 shadow-lg border border-white/30">
            <h3 className="text-white text-lg font-semibold mb-2">Scene Description</h3>
            <p className="text-white">{currentSceneData?.description || "No description available"}</p>
          </div> */}
        </div>
        
        {/* Audio player */}
        <div className="mb-4">
          <audio 
            ref={audioRef}
            onEnded={() => {
              console.log("Audio ended for scene:", currentScene);
              setIsPlaying(false);
              setIsAudioFinished(true);
            }}
            className="w-full"
            controls
            preload="auto"
          >
            {/* We don't use source element here because we're setting src dynamically in code */}
            Your browser does not support the audio element.
          </audio>
        </div>
        
        {/* Navigation */}
        <div className="flex justify-center">
          <button
            onClick={goToNextScene}
            disabled={!isAudioFinished}
            className={`flex items-center gap-2 px-8 py-3 rounded-full transition-all ${
              isAudioFinished 
                ? "bg-gradient-to-r from-orange-400 to-yellow-400 text-white hover:scale-105" 
                : "bg-gray-400 text-gray-200 cursor-not-allowed opacity-70"
            }`}
          >
            Next <FontAwesomeIcon icon={faArrowRight} />
          </button>
        </div>
      </div>
    );
  };

  // Inject CSS styles for highlighting
  useEffect(() => {
    // Create style element
    const styleElement = document.createElement('style');
    styleElement.innerHTML = highlightStyles;
    document.head.appendChild(styleElement);

    // Cleanup on unmount
    return () => {
      document.head.removeChild(styleElement);
    };
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-yellow-300 via-amber-400 to-orange-400 p-6">
      {/* Navigation */}
      <div className="max-w-4xl mx-auto mb-8 flex justify-between items-center">
        <Link 
          to="/" 
          className="bg-gradient-to-br from-orange-300 to-yellow-300 p-3 rounded-full shadow-lg hover:scale-105 transition-transform inline-block"
        >
          <FontAwesomeIcon icon={faHome} className="text-xl text-white" />
        </Link>
        
        {/* Character avatar - only show in chat mode */}
        {!showStoryPlayback && storyData?.stories[0]?.character_image_path && (
          <div className="w-[100px] h-[100px] rounded-full overflow-hidden border-4 border-white/70 shadow-lg">
            <img 
              src={storyData.stories[0].character_image_path.startsWith('http') ? 
                storyData.stories[0].character_image_path : 
                `${API_URL}${storyData.stories[0].character_image_path}`} 
              alt={storyData.stories[0].character_name || "Alien Character"}
              className="w-full h-full object-cover" 
            />
          </div>
        )}
      </div>

      {/* Main content - either story playback or chat */}
      <div className="max-w-4xl mx-auto">
        {showStoryPlayback ? (
          <div className="bg-white/20 backdrop-blur-lg rounded-3xl p-4 mb-6 h-[70vh] overflow-hidden border-2 border-white/30 shadow-2xl">
            {renderStoryPlayback()}
          </div>
        ) : (
          <>
            {/* Chat header with character name */}
            <div className="bg-white/20 backdrop-blur-lg rounded-t-3xl p-4 flex items-center border-2 border-white/30 border-b-0 shadow-lg">
              <div className="text-white">
                <h2 className="text-xl font-bold flex items-center">
                  <span className="mr-2">👽</span>
                  {storyData?.stories[0]?.character_name || "Zorb"}
                </h2>
                <p className="text-sm opacity-70">Alien Friend</p>
              </div>
            </div>
            
            {/* Chat Container */}
            <div className="bg-white/20 backdrop-blur-lg rounded-b-3xl p-6 mb-6 h-[55vh] overflow-y-auto chat-container border-2 border-white/30 border-t-0 shadow-2xl">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`message flex ${
                    message.sender === 'user' ? 'justify-end' : 'justify-start'
                  } mb-4`}
                >
                  <div
                    className={`${message.sender === 'alien' ? 'alien-message' : ''} max-w-[80%] p-4 rounded-2xl shadow-lg ${
                      message.sender === 'user'
                        ? 'bg-gradient-to-r from-orange-400 to-yellow-400 text-white'
                        : 'bg-gradient-to-r from-yellow-300 to-amber-300 text-white transition-all duration-300'
                    }`}
                  >
                    {message.sender === 'alien' && (
                      <div className="text-sm opacity-70 mb-1 flex items-center gap-2">
                        {storyData?.stories[0]?.character_name || "Zorb"} <span className="text-base">👽</span>
                      </div>
                    )}
                    <p className="text-lg">{message.text}</p>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Message Input and Voice Chat */}
            {!isPlayingResponse ? (
              <div className="flex justify-center">
                {/* Voice Input Button */}
                <button
                  type="button"
                  onClick={toggleRecording}
                  className={`${
                    isRecording 
                      ? "bg-red-500 hover:bg-red-600" 
                      : "bg-gradient-to-r from-orange-400 to-yellow-400 hover:from-orange-500 hover:to-yellow-500"
                  } text-white rounded-full p-5 transition-all hover:scale-105 shadow-lg`}
                >
                  <FontAwesomeIcon icon={isRecording ? faStop : faMicrophone} className="text-xl" />
                </button>
              </div>
            ) : (
              <div className="flex justify-center py-4 text-white/80 italic">
                <p>Alien is speaking...</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default Chat; 