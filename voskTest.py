import vosk
import pyaudio
import json

model = vosk.Model("vosk/vosk-model-small-hi-0.22")
rec = vosk.KaldiRecognizer(model, 16000)
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
stream.start_stream()
print("Say something...")

while True:
    data = stream.read(4000, exception_on_overflow=False)
    if rec.AcceptWaveform(data):
        print(json.loads(rec.Result()))
    else:
        print(rec.PartialResult())