"""All texts the bot sends to the owner (Turkish). HTML parse mode."""

HELP = (
    "🎬 <b>Roblox Video Botu</b>\n\n"
    "<b>Video üretmek için:</b>\n"
    "1️⃣ Önce <b>MP3 seslendirmeni</b> gönder.\n"
    "2️⃣ Sonra o MP3 mesajına <b>yanıt (Reply)</b> vererek <b>senaryo dosyasını</b> (.txt) gönder.\n"
    "   (Sırası tersi de olur: önce senaryo, sonra ona yanıt olarak MP3.)\n\n"
    "<b>Komutlar</b>\n"
    "/test – hızlı demo video (düşük kalite, yaklaşık 20 sn)\n"
    "/testhd – 1080p 60 fps demo (kaliteyi ve hızı ölçmek için)\n"
    "/status – çalışan işler\n"
    "/cancel – çalışan işleri durdur\n"
    "/id – sohbet numaran\n"
    "/help – bu yardım"
)

NOT_ALLOWED = "⛔ Bu bot özel kullanım içindir."
ID_TEXT = "🆔 Sohbet numaran: <code>{chat_id}</code>\nBunu GitHub'da <b>ALLOWED_CHAT_ID</b> secret'ı olarak kaydet."
NEED_ID = ("🔐 Güvenlik için bot henüz sadece sahibine bağlı değil.\n"
           "Sohbet numaran: <code>{chat_id}</code>\nGitHub → Settings → Secrets → <b>ALLOWED_CHAT_ID</b> adıyla kaydet, sonra tekrar dene.")
GOT_AUDIO = "🎧 Ses dosyasını aldım. Şimdi bu mesaja <b>yanıt vererek</b> senaryo dosyasını (.txt) gönder."
GOT_STORY = ("📝 Senaryoyu aldım: <b>{shots}</b> sahne, <b>{words}</b> kelime.\n"
             "Şimdi MP3 seslendirme mesajına <b>yanıt vererek</b> bu senaryo dosyasını tekrar gönder, ya da önce MP3'ü gönderip ona yanıt ver.")
BAD_STORY = ("⚠️ Senaryo dosyasında sahne bulamadım.\n"
             "Her sahne satırı <code>konum | kamera | karakterler | eşyalar :: anlatım</code> biçiminde olmalı (<code>::</code> zorunlu).")
TOO_BIG = "⚠️ Senaryo çok uzun ({chars} karakter). En fazla {limit} karakter olabilir."
AUDIO_TOO_BIG = "⚠️ Ses dosyası çok büyük (en fazla 20 MB). MP3 olarak, daha düşük bitrate ile tekrar gönder."
STARTED = ("🚀 <b>Üretim başladı</b>\n"
           "• Sahne: <b>{shots}</b>\n• Kalite: <b>{quality}</b>\n"
           "İlerlemeyi yüzde olarak yazacağım.")
DEMO_STARTED = "🧪 <b>Demo üretimi başladı</b> ({quality}). Birkaç dakika sürer."
PLAN_READY = ("📋 Plan hazır: <b>{shots}</b> sahne, <b>{seconds}</b> sn video.\n"
              "Ses hizalama: {align}\n⏳ <b>%{pct}</b> tamamlandı • %{left} kaldı")
PROGRESS = "⏳ <b>%{pct}</b> tamamlandı • %{left} kaldı\n{stage}{eta}"
STAGE_RENDER = "🎞 Kareler çiziliyor ({done}/{total} parça)"
STAGE_ASSEMBLE = "🔧 Parçalar birleştiriliyor, ses ekleniyor"
ETA = "\n⌛ Tahmini kalan: ~{minutes} dk"
DONE_VIDEO = "✅ <b>Video hazır!</b> (%100)\n⏱ {duration} sn • 📦 {size} MB\n🔗 Tam kalite (1080p): {link}"
DONE_LINK = "✅ <b>Video hazır!</b> (%100)\n⏱ {duration} sn • 📦 {size} MB\nTelegram sınırını aştığı için indirme bağlantısı:\n🔗 {link}"
FAILED = "❌ <b>Üretim başarısız oldu.</b>\nAyrıntı için GitHub kaydına bak:\n{url}"
CANCELLED = "🛑 {n} iş durduruldu."
NO_JOBS = "Çalışan iş yok."
STATUS_ROW = "• {name} – {status}"
