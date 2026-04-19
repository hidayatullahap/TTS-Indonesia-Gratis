import sys
import requests
import argparse
from simpleaudio import WaveObject
import os

def play_audio(file_path):
    try:
        obj = WaveObject.from_wave_file(file_path)
        p = obj.play()
        p.wait_done()
    except Exception as e:
        print(f"Error playing audio: {e}")

def main():
    parser = argparse.ArgumentParser(description="Instant TTS Client")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument("--speaker", default="ardi", help="Speaker name (ardi, wibowo, gadis, etc.)")
    parser.add_argument("--host", default="127.0.0.1", help="Server host")
    parser.add_argument("--port", default="8000", help="Server port")
    parser.add_argument("--save", action="store_true", help="Keep the downloaded wav file")
    
    args = parser.parse_args()
    
    url = f"http://{args.host}:{args.port}/generate"
    temp_file = "client_last_speech.wav"
    
    try:
        # Send request to server
        response = requests.post(url, json={"text": args.text, "speaker": args.speaker}, timeout=30)
        
        if response.status_code == 200:
            with open(temp_file, "wb") as f:
                f.write(response.content)
            
            # Play the sound
            play_audio(temp_file)
            
            if not args.save:
                try:
                    os.remove(temp_file)
                except:
                    pass
        else:
            print(f"Server Error ({response.status_code}): {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the TTS server. Is 'server.py' running?")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
