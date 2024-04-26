from dotenv import load_dotenv
import logging, verboselogs
from time import sleep
from deepgram import DeepgramClient, DeepgramClientOptions, LiveTranscriptionEvents, LiveOptions, Microphone

load_dotenv()

class DeepgramTranscriber:
    def __init__(self, input_device_index=3):
        self.input_device_index = input_device_index
        self.is_finals = []

        # Create a Deepgram client
        self.deepgram = DeepgramClient()

        # Set up event handlers
        # self.setup_event_handlers()

    def on_open(self, open, **kwargs):
        print("Deepgram Connection Open")

    def on_message(self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if len(sentence) == 0:
            return
        if result.is_final:
            self.is_finals.append(sentence)
            if result.speech_final:
                utterance = ' '.join(self.is_finals)
                print(f"Speech Final: {utterance}")
                self.is_finals = []
            else:
                print(f"Is Final: {sentence}")
        else:
            print(f"Interim Results: {sentence}")

    def on_metadata(self, metadata, **kwargs):
        print(f"Deepgram Metadata: {metadata}")

    def on_speech_started(self, speech_started, **kwargs):
        print("Deepgram Speech Started")

    def on_utterance_end(self, utterance_end, **kwargs):
        if self.is_finals:
            utterance = ' '.join(self.is_finals)
            print(f"Deepgram Utterance End: {utterance}")
            self.is_finals = []

    def on_close(self, close, **kwargs):
        print("Deepgram Connection Closed")

    def on_error(self, error, **kwargs):
        print(f"Deepgram Handled Error: {error}")

    def on_unhandled(self, unhandled, **kwargs):
        print("Deepgram Unhandled Websocket Message: {unhandled}")

    def transcribe(self):

        connection = self.deepgram.listen.live.v("1")
        self.deepgram.listen.live.v("1").on(LiveTranscriptionEvents.Open, self.on_open)
        self.deepgram.listen.live.v("1").on(LiveTranscriptionEvents.Transcript, self.on_message)
        self.deepgram.listen.live.v("1").on(LiveTranscriptionEvents.Metadata, self.on_metadata)
        self.deepgram.listen.live.v("1").on(LiveTranscriptionEvents.SpeechStarted, self.on_speech_started)
        self.deepgram.listen.live.v("1").on(LiveTranscriptionEvents.UtteranceEnd, self.on_utterance_end)
        self.deepgram.listen.live.v("1").on(LiveTranscriptionEvents.Close, self.on_close)
        self.deepgram.listen.live.v("1").on(LiveTranscriptionEvents.Error, self.on_error)
        self.deepgram.listen.live.v("1").on(LiveTranscriptionEvents.Unhandled, self.on_unhandled)

        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=48000,
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            endpointing=300
        )

        addons = {"no_delay": "true"}

        if not connection.start(options, addons=addons):
            print("Failed to connect to Deepgram")
            return

        # Microphone handling
        microphone = Microphone(
            self.deepgram.listen.live.v("1").send,
            input_device_index=self.input_device_index,
            rate=48000
        )

        microphone.start()
        sleep(5)  # Adjust sleep duration based on needs
        microphone.finish()

        self.deepgram.listen.live.v("1").finish()
        print("Finished transcription process")

if __name__ == "__main__":
    transcriber = DeepgramTranscriber()
    transcriber.transcribe()
