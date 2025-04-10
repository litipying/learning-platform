# Space English Learning App

A fun and educational application that transforms daily news into child-friendly alien stories, complete with vocabulary lessons and audio narration. Perfect for children aged 6-10 years old learning English.

## Features

- 🌍 Converts real-world news into child-friendly alien stories
- 📚 Includes 3 vocabulary words with explanations and example sentences
- 🎧 Audio narration using ElevenLabs text-to-speech
- 📅 Daily updates at midnight (HKT)
- 🗃️ SQLite database storage
- 🐳 Docker support for easy deployment

## Prerequisites

- Docker and Docker Compose
- News API key (from [newsapi.org](https://newsapi.org))
- OpenRouter API key (from [openrouter.ai](https://openrouter.ai))
- ElevenLabs API key (from [elevenlabs.io](https://elevenlabs.io))

## Project Structure

```
.
├── cron/               # Cron job for news fetching
├── data/               # Data storage
│   ├── audio/         # Generated audio files
│   └── news.db        # SQLite database
├── docker-compose.yml  # Docker configuration
└── .env               # Environment variables
```

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd learning-platform
```

2. Create a `.env` file in the root directory:
```bash
# API Keys
NEWS_API_KEY=your_newsapi_key
OPENAI_API_KEY=your_openrouter_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# Optional: Custom ports
API_PORT=8003
```

3. Create necessary directories:
```bash
mkdir -p data/audio
```

4. Build and start the containers:
```bash
docker-compose up --build -d
```

## Audio Files

Audio files are stored in the `data/audio` directory with filenames in the format:
```
alien_news_YYYYMMDD_HHMMSS.mp3
```

## Development

To run the services individually:

1. Cron service:
```bash
cd cron
pip install -r requirements.txt
python main.py
```

## Troubleshooting

1. If audio files aren't generating:
   - Check your ElevenLabs API key
   - Ensure the `data/audio` directory exists and has write permissions

2. If news isn't updating:
   - Verify your News API key
   - Check the logs: `docker-compose logs cron`

## License

This project is licensed under the MIT License - see the LICENSE file for details. 