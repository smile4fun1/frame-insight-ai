# Video Analysis App

This project consists of a FastAPI backend and a React + Vite frontend for analyzing videos using FFmpeg and GPT-4.

## Project Structure

```
video-analysis-app/
├── backend/
│   ├── venv/
│   ├── main.py
│   ├── requirements.txt
│   ├── setup.py
│   └── cache/
└── frontend/
    ├── public/
    ├── src/
    │   ├── App.jsx
    │   ├── App.css
    │   └── main.jsx
    ├── package.json
    └── vite.config.js
```

## Prerequisites

- Python 3.7+
- Node.js 14+
- npm 6+
- OpenAI API key
- FFmpeg (installed and available in system PATH)

## Installation and Setup

### FFmpeg Installation

1. Download FFmpeg from the official website: https://ffmpeg.org/download.html
2. Extract the downloaded archive
3. Add the path to the FFmpeg `bin` folder to your system's PATH environment variable

### Backend

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the backend package:
   ```
   pip install -e .
   ```

4. Create a `.env` file in the backend directory and add your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

5. Create a `cache` directory in the backend folder:
   ```
   mkdir cache
   ```

### Frontend

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install the required packages:
   ```
   npm install
   ```

## Running the Application

### Backend

1. From the backend directory, activate the virtual environment if not already activated:
   ```
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

2. Run the FastAPI server:
   ```
   uvicorn main:app --reload
   ```

The backend will be available at `http://localhost:8000`.

### Frontend

1. From the frontend directory, run the development server:
   ```
   npm run dev
   ```

The frontend will be available at `http://localhost:5173`.

## Usage

1. Open your web browser and go to `http://localhost:5173`.
2. (Optional) Click the "Clear Cache" button to remove any stored analysis results.
3. Select a video file using the file input.
4. Choose an analysis type from the dropdown menu:
   - General Analysis
   - UI Interaction Analysis
   - Emotion Detection
   - Object Detection
   - Text Recognition
   - Custom (allows you to enter a custom prompt)
5. If you selected "Custom", enter your custom analysis prompt.
6. Click "Upload and Analyze" to process the video.
7. For large videos, you'll see a progress bar indicating the upload and processing progress.
8. Once complete, the app will display:
   - The filename of the uploaded video
   - The selected analysis type (and custom prompt if applicable)
   - For each chunk (if applicable):
     - The number of frames extracted
     - The GPT-4 analysis of the video content based on the selected analysis type
9. You can download the analysis results in JSON, PDF, or Markdown format using the provided download buttons.

## Features

- Video upload and frame extraction using FFmpeg
- GPT-4 integration for video content analysis
- User-friendly interface with error handling and loading states
- Responsive design for various screen sizes
- Caching mechanism for processed videos to improve performance
- Support for large video files through chunked uploads and progressive analysis
- Multiple predefined analysis types and custom prompt option
- Download analysis results in JSON, PDF, or Markdown format
- Clear cache functionality to remove stored analysis results

## Troubleshooting

If you encounter issues:

1. Ensure FFmpeg is correctly installed and available in your system PATH
2. Check that your OpenAI API key is correctly set in the `.env` file
3. Verify that you have sufficient credits in your OpenAI account
4. Confirm that you have access to the GPT-4 API with vision capabilities
5. If you're getting unexpected results, try clearing the cache using the "Clear Cache" button

For other issues, check the console logs in both the frontend and backend for error messages.

## Contributing

Contributions to improve the app are welcome. Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License.
