# 🚢 Carnival Cruises - TikTok Profile Analyzer

Complete pipeline for TikTok audience analysis for Carnival Cruises, including data extraction, media download, and AI analysis.

## 📋 Description

This project implements a full pipeline for analyzing TikTok profiles that have commented on Carnival Cruises content. The system extracts user information, downloads multimedia, and performs advanced AI analysis to identify high-value prospects.

## 🏗️ Project Structure

```
tik_tok_profiles_analyzer/
├── main.py                          # Main pipeline script
├── scripts/                         # Pipeline scripts
│   ├── tiktok_api_analyzer.py       # API data extraction
│   ├── tiktok_media_downloader.py   # Media download
│   └── carnival_analyzer_integrated.py # AI analysis
├── data/                            # Input and output data
│   ├── Input/
│   │   └── analysis_prompt.txt      # AI analysis prompt
│   └── Output/                      # Pipeline results
├── logs/                            # Execution logs
├── config/                          # Configuration files
│   ├── config_api.ini
│   ├── config_company.ini
│   └── config_multimedia.ini
├── requirements.txt                 # Python dependencies
```

## 🚀 Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd tik_tok_profiles_analyzer
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure the configuration files

#### config/config_api.ini
```ini
[tiktok_api]
rapidapi_key = your_api_key_here
rapidapi_host = tiktok-api23.p.rapidapi.com

[tiktok_scraper_api]
rapidapi_key = your_api_key_here
rapidapi_host = tiktok-scraper7.p.rapidapi.com

[video_detail_api]
rapidapi_key = your_api_key_here
rapidapi_host = tiktok-api23.p.rapidapi.com
endpoint = /api/video/detail

[general_config]
output_base_dir = data/Output
max_retries = 3
request_timeout = 30

[testing]
test_username = shalom_mainnnnn
```

#### config/config_company.ini
```ini
[company_api]
api_key = your_dify_api_key_here
api_url = https://dify-api.factory.tools/service/api/v1/chat-messages
```

#### config/config_multimedia.ini
```ini
[ffmpeg]
ffmpeg_path = C:\path\to\ffmpeg\bin\ffmpeg.exe

[media_processing]
max_videos_per_user = 15
download_timeout = 30
enable_audio_extraction = true
enable_screenshot_extraction = true
```

## 🔄 Pipeline Execution

### Full Execution
```bash
python main.py
```

The main script automatically runs the 3 pipeline steps:

1. **Data Extraction** (`tiktok_api_analyzer.py`)
   - Gets basic user info
   - Extracts video list
   - Gets specific video details

2. **Media Download** (`tiktok_media_downloader.py`)
   - Downloads TikTok videos
   - Extracts audio from videos
   - Downloads post images

3. **AI Analysis** (`carnival_analyzer_integrated.py`)
   - Processes downloaded media
   - Extracts audio transcriptions
   - Performs OCR on screenshots
   - Sends full analysis to Dify API
   - Generates final YAML report

### Individual Execution

If you need to run only a specific step:

```bash
# Data extraction only
python scripts/tiktok_api_analyzer.py

# Media download only
python scripts/tiktok_media_downloader.py

# AI analysis only
python scripts/carnival_analyzer_integrated.py
```

## 📊 Results

### Output Structure
```
data/Output/
├── user_info/                      # User information
│   └── {username}_user_info.yml
├── videos_info/                    # Video information
│   └── {username}_videos.yml
├── video_details/                  # Specific details
│   └── video_details_batch.yml
├── media/                          # Downloaded media
│   └── {username}/
│       ├── videos/                 # Downloaded videos
│       ├── audio/                  # Extracted audio
│       ├── images/                 # Downloaded images
│       └── media_download_results.yml
└── carnival_analysis/              # Final analysis
    └── {username}_carnival_analysis_{timestamp}.yml
```

### Logs
```
logs/
└── pipeline_log_{timestamp}.txt    # Full execution log
```

## 🎯 Audience Analysis

The system classifies profiles into the following categories:

- **INDIVIDUAL_PERSON**: Real people (students, professionals, families)
- **CONTENT_CREATOR**: Content creators (influencers, bloggers)
- **LOCAL_BUSINESS**: Local businesses (restaurants, shops)
- **CORPORATE_BUSINESS**: Large companies
- **HOME_BUSINESS**: Home-based businesses
- **EDUCATIONAL_MOTIVATIONAL**: Educators and coaches
- **ARTISTIC_ENTERTAINMENT**: Artists and entertainment
- **ORGANIZATION_INSTITUTION**: Organizations and institutions

### Value Metrics for Carnival

- **High Value**: Multigenerational families, frequent travelers, family-friendly content creators
- **Medium Value**: Young professionals, couples without children, occasional travelers
- **Low Value**: Inactive accounts, inappropriate content, bots

## 🔧 Advanced Configuration

### Customize Test User
Edit `config/config_api.ini` in the `[testing]` section:
```ini
[testing]
test_username = your_test_user
```

### Adjust Download Limits
In `config/config_multimedia.ini`:
```ini
[media_processing]
max_videos_per_user = 10  # Lower for testing
download_timeout = 60     # Increase for slow connections
```

### Configure FFmpeg
Make sure the FFmpeg path is correct in `config/config_multimedia.ini`:
```ini
[ffmpeg]
ffmpeg_path = C:\Users\your_user\Downloads\ffmpeg\bin\ffmpeg.exe
```

## 🐛 Troubleshooting

### API Key Error
- Make sure all API keys are set correctly
- Ensure your RapidAPI accounts have available credits

### FFmpeg Error
- Download FFmpeg from https://ffmpeg.org/download.html
- Update the path in `config/config_multimedia.ini`

### Dependency Error
```bash
pip install --upgrade -r requirements.txt
```

### Detailed Logs
Check the logs in `logs/pipeline_log_{timestamp}.txt` for detailed error information.

## 📈 Monitoring and Metrics

The pipeline generates detailed metrics:

- **Execution time** per script
- **Download success rate**
- **Extracted data quality**
- **Audience analysis** by category

## 🔒 Security and Privacy

- API keys are stored in local configuration files
- Data is processed locally
- No personal data is shared with third parties
- Complies with TikTok privacy policies

## 📞 Support

For issues or questions:
1. Check the logs in `logs/`
2. Verify the configuration in the `.ini` files
3. Make sure all dependencies are installed

## 📄 License

This project is for internal use by Carnival Cruises.

---

**Developed for Carnival Cruises - TikTok Audience Analysis 2024-2025** 