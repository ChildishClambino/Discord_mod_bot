from elevenlabs import set_api_key, voices

set_api_key("sk_dfc921baa43500bf001c7fe224e07cc90877a7cbfdf9eca3")

for voice in voices():
    print(f"{voice.name} — {voice.voice_id}")
