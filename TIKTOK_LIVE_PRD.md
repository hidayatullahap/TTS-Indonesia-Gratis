# PRD: TikTok Live TTS Desktop Integration

## 1. Objective
Create a simple, standalone Desktop Application that connects to a TikTok Live stream, reads incoming comments, and converts them to speech using the optimized in-process TTS engine. The app will ensure comments are spoken sequentially without overlapping audio.

## 2. Background & Motivation
The user wants to actively read out comments from a TikTok Live stream using the previously optimized TTS engine. While the TTS engine can currently be run via CLI or Web UI, a dedicated desktop application is required to seamlessly connect to the TikTok Live API (`TikTokLive` library), listen to real-time chat events, and play the TTS audio sequentially without blocking the asynchronous event loop or causing audio overlap.

## 3. Scope & Impact
- **In Scope:**
  - Create a new desktop interface using `CustomTkinter`.
  - Provide an input field for the TikTok username.
  - Provide a dropdown to select the TTS speaker (e.g., Ardi, Wibowo, Gadis, Juminten, Asep).
  - Provide Start and Stop buttons to connect/disconnect from the TikTok Live stream.
  - Integrate the `TikTokLive` Python library to listen for `CommentEvent`.
  - Integrate the optimized in-process `tts` function to avoid load times.
  - Implement a thread-safe queue to process and play comments sequentially without overlap.
- **Out of Scope:**
  - Support for reading gifts, likes, or shares (only text comments for now).
  - Complex UI animations, chat history display, or multi-stream support.

## 4. Proposed Solution
- **UI Framework:** CustomTkinter. It provides a modern, dark-themed, and lightweight interface that fits perfectly for utility desktop apps.
- **Architecture:** All-in-One Process. The desktop application will initialize the TTS engine in memory upon startup or when playback begins, avoiding the complexity of running a separate API server.
- **Event Loop & Queueing Strategy:**
  - `TikTokLive` requires `asyncio` to maintain the WebSocket connection.
  - When a comment arrives, it will be pushed into a standard thread-safe queue (`queue.Queue`).
  - A dedicated background worker thread will consume the queue, run the blocking `tts` generation, and play the audio using `simpleaudio` (which includes the blocking `p.wait_done()`). 
  - This architecture ensures the `asyncio` loop handling TikTok events is never blocked, and audio plays sequentially, naturally preventing overlap.

## 5. Implementation Plan
- **Step 1:** Add dependencies to the environment (`TikTokLive`, `customtkinter`). WITH VERSION tiktoklive==6.6.5 and pyee<12
- **Step 2:** Create the core application script (`tiktok_app.py`) containing the CustomTkinter UI layout (Username input, Speaker dropdown, Start/Stop buttons, Status/Log label).
- **Step 3:** Implement the backend logic:
  - Initialize the `TikTokLiveClient`.
  - Setup the `on_comment` event listener to push comments into the queue.
- **Step 4:** Implement the TTS Worker Thread:
  - Continuously read from the queue.
  - Clean the comment text (remove emojis/unsupported chars if necessary).
  - Generate the TTS audio using the `tts` function from `g2p_id.scripts.tts`.
  - Play the generated WAV file.
  - Wait for the audio to finish before processing the next item.
- **Step 5:** Connect UI buttons to start/stop the `asyncio` event loop running the TikTok client gracefully in a separate thread.

## 6. Verification
- Verify the CustomTkinter app launches successfully.
- Verify the user can input a TikTok username and connect to an active live stream.
- Verify that when comments arrive rapidly, they are queued and spoken one by one without audio overlap.
- Verify the Start/Stop buttons correctly start and terminate the connection and worker thread.
