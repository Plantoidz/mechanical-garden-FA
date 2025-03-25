from RealtimeSTT import AudioToTextRecorder

def process_text(text):
    print(text)


if __name__ == '__main__':

    utterance = ""

    print("Wait until it says 'speak now'")
    with AudioToTextRecorder() as recorder:

        # recorder = AudioToTextRecorder(
        #     # input_device_index=7,
        #     enable_realtime_transcription=True,
        #     use_main_model_for_realtime=True,
        #     print_transcription_time=True,
        #     on_realtime_transcription_update=process_text,
        # )

        utterance = recorder.text()

        # recorder.start()
        # recorder.text(process_text)
        # recorder.stop()
        # recorder.shutdown()

    print("Utterance is:", utterance)
        # i = 0

        # while True:
        #     recorder.text(process_text)
        #     print(f"Loop {i}")
        #     i += 1
        #     if i == 2:
        #         recorder.stop()
        #         recorder.shutdown()
        #         break