from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions, Microphone

class DeepgramTranscription:
    def __init__(self, sample_rate: int = 48000, device_index: int = 0):
        self.deepgram = DeepgramClient()
        self.is_finals = []
        self.final_result = ""
        self.transcription_complete = False  # New flag for completion
        self.sample_rate = sample_rate
        self.device_index = device_index
        
    def on_message(self, *args, **kwargs):
        result = kwargs.get('result', None)
        if result is None and args:
            result = args[0]  # Assuming result is the first positional argument

        sentence = result.channel.alternatives[0].transcript
        if not sentence:
            return

        if result.is_final:
            self.is_finals.append(sentence)

            if result.speech_final:
                self.final_result = ' '.join(self.is_finals)
                print(f"Speech Final: {self.final_result}")
                self.transcription_complete = True  # Set completion flag
                self.is_finals = []
            else:
                print(f"Is Final: {sentence}")
        else:
            print(f"Interim Results: {sentence}")

    def start_listening(self):
        connection = self.deepgram.listen.live.v("1")
        connection.on(LiveTranscriptionEvents.Transcript, self.on_message)

        options = LiveOptions(
            model="nova-2",
            language="en-US",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=self.sample_rate,
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            endpointing=300
        )

        if connection.start(options) is False:
            print("Failed to connect to Deepgram")
            return

        microphone = Microphone(
            connection.send,
            input_device_index=self.device_index,
            rate=self.sample_rate,
        )

        microphone.start()

        # Wait until the final result is ready
        while not self.transcription_complete:
            pass

        microphone.finish()
        connection.finish()

    def get_final_result(self):
        return self.final_result

# todo: implement saving