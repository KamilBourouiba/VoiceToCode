import pyaudio
import wave
import whisper
import threading
import json
from openai import OpenAI

client = OpenAI(api_key='OPENAIKEY')

# Constants for audio recording
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "recorded_audio.wav"
TRANSCRIPT_FILENAME = "transcript.txt"
INSTRUCT_JSON_FILENAME = "instruction.json"

def record_audio():
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    frames = []
    print("Recording started. Press Enter to stop recording.")
    while recording_flag.is_set():
        data = stream.read(CHUNK)
        frames.append(data)
    print("Recording stopped.")
    stream.stop_stream()
    stream.close()
    audio.terminate()
    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
    print(f"Audio saved to {WAVE_OUTPUT_FILENAME}")

def transcribe_audio(audio_file, model_size='large'):
    model = whisper.load_model(model_size)
    result = model.transcribe(audio_file)
    return result['text'] if 'text' in result else ''

def send_to_chatgpt(transcription):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": 'You give a json answer in this format : {"Instruct": "String", "From": Int, "Code": "string"}. For example if the user asks to paste code related to a bubble swap from line 1 you give this : {"Instruct": "paste", "From": 1, "Code": "def bubble_sort(arr): return [arr.__setitem__(j, arr[j+1]) or arr.__setitem__(j+1, arr[j]) for i in range(len(arr)) for j in range(len(arr)-i-1) if arr[j] > arr[j+1]] or arr"}. Only Python code. If user asks to delete return a json like this : {"Instruct": "delete", "From": 1,"To": 10}'},
            {"role": "user", "content": transcription}
        ]
    )
    return response.choices[0].message

def main():
    global recording_flag
    recording_flag = threading.Event()

    while True:
        command = input("Type 'start' to begin recording, or 'exit' to quit, and press Enter: ").strip().lower()
        if command == "start":
            recording_flag.set()
            recording_thread = threading.Thread(target=record_audio)
            recording_thread.start()
            input("Press Enter to stop recording...")
            recording_flag.clear()
            recording_thread.join()
            print("Transcribing audio...")
            transcription_text = transcribe_audio(WAVE_OUTPUT_FILENAME)
            print("Transcription:\n", transcription_text)
            
            with open(TRANSCRIPT_FILENAME, 'w') as trans_file:
                trans_file.write(transcription_text)
            print(f"Transcription saved to {TRANSCRIPT_FILENAME}")

            print("Sending transcription to ChatGPT...")
            
            gpt_response = send_to_chatgpt(transcription_text)

            print("ChatGPT Response:\n", gpt_response)

            content = gpt_response.content

            try:
                instruction_json = json.loads(content)
                with open(INSTRUCT_JSON_FILENAME, 'w') as f:
                    json.dump(instruction_json, f, indent=4)
                print(f"Instructions saved to {INSTRUCT_JSON_FILENAME}")
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON content from ChatGPT: {e}")
                print("Content:", content)
            except KeyError:
                print("Unexpected response structure from ChatGPT.")
                print("ChatGPT response:", gpt_response)


        elif command == "exit":
            break
        else:
            print("Unknown command. Please type 'start' to record, or 'exit' to quit.")

if __name__ == "__main__":
    main()
