# Space English Learning App

A fun and educational application that transforms daily news into child-friendly alien stories and generates interactive adventure stories with alien characters. Perfect for children aged 6-10 years old learning English.

## Features

### News Feature
- 🌍 Converts real-world news into child-friendly alien stories
- 📚 Includes 3 vocabulary words with explanations and example sentences
- 🎧 Audio narration using ElevenLabs text-to-speech
- 📺 Animated talking videos using D-ID service
- 📅 Daily updates at midnight (HKT)

### Adventure Story Feature
- 👽 Random alien character generation with unique personalities
- 🚀 Interactive 4-scene adventure stories with visual scenes
- 🎤 Audio narration for each scene
- 💬 Character chat interface for interacting with the story character
- 🎮 Story playback interface with sequential scene navigation
- 🗣️ Voice input capabilities for conversing with alien characters

### Technical Features
- 🗃️ Dual SQLite database system (news.db and story.db)
- 🌐 FastAPI backend with dedicated routes for news and stories
- ⚛️ React frontend with audio playback and chat functionality
- 🐳 Docker support for easy deployment
- 🧠 Gemini AI for content and image generation
- 🎵 ElevenLabs for text-to-speech and speech-to-text conversion

## Prerequisites

- Docker and Docker Compose
- News API key (from [newsapi.org](https://newsapi.org))
- Google Gemini API key (from [Google AI Studio](https://makersuite.google.com/app/apikey))
- ElevenLabs API key (from [elevenlabs.io](https://elevenlabs.io))
- D-ID API key (from [d-id.com](https://www.d-id.com))
- RunningHub API key (optional, for alternative video generation)

## Project Structure

```
.
├── api/                # FastAPI backend
│   ├── main.py        # API routes and database models
│   └── requirements.txt # API dependencies
├── cron/               # Cron jobs for news and story generation
│   ├── main.py        # Entry point and scheduler
│   ├── app.py         # Streamlit demo application
│   ├── story.py       # Adventure story generation
│   ├── did_service.py # D-ID video generation service
│   └── runninghub_service.py # RunningHub video generation service
├── data/               # Data storage
│   ├── audio/         # Generated audio files for news
│   ├── text/          # Generated text content
│   ├── images/        # Generated images
│   ├── videos/        # Generated video files
│   ├── news.db        # SQLite database for news
│   ├── story.db       # SQLite database for adventure stories
│   └── story/         # Adventure story assets
│       ├── character/ # Character images
│       ├── scene/     # Scene images
│       └── voice/     # Scene audio narrations
├── frontend/           # React.js frontend application
│   ├── src/           # Source code
│   │   ├── pages/     # Page components
│   │   └── components/ # Reusable components
│   ├── public/        # Static assets
│   └── package.json   # Dependencies and scripts
├── docker-compose.yml  # Docker configuration
└── .env               # Environment variables
```

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd space-english-app
```

2. Create a `.env` file in the root directory using the example below:
```bash
# API Keys
NEWS_API_KEY=your_newsapi_key
GEMINI_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_key
DID_API_KEY=your_did_api_key
RUNNINGHUB_API_KEY=your_runninghub_key

# API Configuration
API_BASE_URL=http://localhost:8003

# Frontend Configuration
VITE_API_URL=http://localhost:8003

# Optional: Custom ports
API_PORT=8003
FRONTEND_PORT=3000
```

3. Create necessary directories:
```bash
mkdir -p data/audio data/text data/images data/videos data/story/character data/story/scene data/story/voice
```

4. Build and start the containers:
```bash
docker-compose up --build -d
```

## API Endpoints

The API will be available at `http://localhost:8003` (or your custom port)

### News Endpoints
- `GET /news/`: Get all news articles
- `GET /news/{id}`: Get a specific news article
- `DELETE /news/{id}`: Delete a specific news article

### Story Endpoints
- `GET /story/dates`: Get all available dates for stories
- `GET /story/scenes/date/{date}`: Get all scenes from stories for a specific date
  - Query parameter: `latest_only` (boolean) - If true, only returns the latest story for that date
  - Response includes: `image_url` and `audio_url` fields that provide direct URLs to access media files

## Accessing Media Files

The API serves media files through the `/data` endpoint. If you're having trouble accessing images or audio:

1. Ensure the `API_BASE_URL` environment variable is correctly set in your `.env` file (default: `http://localhost:8003`)
2. For the frontend, set `VITE_API_URL` to match your API URL
3. Media URLs are generated using the following pattern:
   ```
   {API_BASE_URL}/data/{path_without_leading_slash}
   ```
4. Check the browser console for any network errors when loading media

## Troubleshooting

### Media Files Not Loading
1. Verify file paths and permissions:
   ```bash
   docker-compose exec api ls -la /app/data
   ```
2. Check API logs for any errors:
   ```bash
   docker-compose logs api
   ```
3. Ensure the data directory is correctly mounted in the Docker container:
   ```bash
   docker-compose exec api ls -la /app/data/story
   ```
4. Verify the API's static file serving:
   ```bash
   curl -I http://localhost:8003/data/story/character/example.png
   ```
5. Check that your browser isn't blocking access to the media files due to CORS issues

### Database Issues
1. If database connections fail:
   - Check that the data directory exists and has proper permissions
   - For story.db issues, ensure the `/app/data` directory is accessible in the Docker container
   - Check logs for any errors: `docker-compose logs api`

2. If adventure stories aren't displaying:
   - Make sure story.db exists and has content
   - Check the API endpoint response: `http://localhost:8003/story/dates`
   - Verify that file paths in the database match the mounted volumes in Docker

### Voice Chat Issues
1. Microphone access denied:
   - Make sure your browser has permission to access the microphone
   - Try using HTTPS instead of HTTP for local development
   - Check browser console for errors

2. Speech-to-text not working:
   - Verify your ElevenLabs API key
   - Check that you have enough credits for the speech-to-text service
   - Ensure the audio recording is correctly formatted

## Development

To run the services individually:

1. API service:
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --reload --port 8003
```

2. News generation:
```bash
cd cron
pip install -r requirements.txt
python main.py --run-now --service did --use-text-to-speech
```

3. Adventure story generation:
```bash
cd cron
pip install -r requirements.txt
python story.py
```

4. Frontend:
```bash
cd frontend
npm install
npm run dev
```

5. Demo interface:
```bash
cd cron
pip install -r requirements.txt
streamlit run app.py
```

## Scripts Reference

### Generate News with Video
```bash
python main.py --run-now --service did --use-text-to-speech --use-character-file --image-service gemini
```

### Generate Adventure Story
```bash
python cron/story.py
```

### Run Demo Interface
```bash
streamlit run cron/app.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.