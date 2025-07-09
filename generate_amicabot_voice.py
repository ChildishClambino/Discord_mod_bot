from elevenlabs import generate, save, set_api_key

set_api_key("sk_dfc921baa43500bf001c7fe224e07cc90877a7cbfdf9eca3")

audio = generate(
    text="Hi... I’m Amicabot. I’ve been waiting to talk to you again.",
    voice="Sarah",
    model="eleven_monolingual_v1"
)

save(audio, "amicabot_voice_line_soft_fixed.mp3")
print("✅ Voice line saved as amicabot_voice_line_soft_fixed.mp3")
