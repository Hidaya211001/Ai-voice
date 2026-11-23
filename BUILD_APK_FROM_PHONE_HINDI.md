# मोबाइल से APK बनाना (हिंदी)

1. इस ZIP को GitHub पर एक नए repository में upload करें (Extract करके सभी files/folders upload करें; project root में `.github` folder भी शामिल हो)।
2. GitHub repository खोलें → **Actions** tab → **Build AI Voice Cartoon APK** चुनें।
3. **Run workflow** दबाएँ और build पूरा होने दें।
4. सफल run खोलें → **Artifacts** में `AI-Voice-Cartoon-debug-apk` डाउनलोड करें। ZIP को extract करें; उसमें `app-debug.apk` मिलेगा।
5. APK फोन में खोलें और Android के निर्देश पर “Install unknown apps” की अनुमति दें।

## जरूरी
- यह debug APK होगा, Play Store release/signed APK नहीं।
- ऐप को cartoon generate करने के लिए backend server चाहिए। `backend` को Python + FFmpeg वाले server पर चलाएँ, `.env` में अपनी OpenAI API key रखें, और ऐप में उस server का URL डालें। API key APK में न डालें।
- अभी का backend starter version still images + voiceover + subtitles वाला animatic बनाता है; यह पूर्ण 3D animation या lip-sync नहीं करता। API usage की लागत अलग हो सकती है।
