# सिर्फ Android मोबाइल से APK बनाने का तरीका

यह तरीका GitHub के cloud runner से APK build करता है; मोबाइल में Android Studio install नहीं करना पड़ता।

## आपको क्या चाहिए
- GitHub account
- Chrome browser
- इस ZIP का extracted project
- Backend को चलाने/host करने के लिए अलग Python hosting या कंप्यूटर (ऐप के generation feature के लिए)

## चरण
1. Chrome में github.com खोलकर account बनाएँ / sign in करें।
2. New repository बनाएँ, उदाहरण: `ai-voice-cartoon`.
3. इस ZIP को फोन में extract करें। GitHub repository में `android_app` folder के अंदर की सभी files और folders upload करें। ध्यान दें: hidden `.github` folder भी upload होना चाहिए।
4. Repository में Actions tab खोलें। यदि GitHub पूछे, "I understand my workflows, go ahead and enable them" चुनें।
5. "Build Android APK" workflow चुनें और "Run workflow" दबाएँ।
6. Build पूरा होने पर workflow run खोलें। नीचे Artifacts में `AI-Voice-Cartoon-debug-apk` डाउनलोड करें।
7. ZIP artifact को फोन में extract करें। `app-debug.apk` पर tap करके install करें। Android पूछे तो Chrome/Files को "Install unknown apps" अनुमति दें।

## जरूरी सुधार / सीमाएँ
- Workflow cloud build के लिए Gradle wrapper न होने पर runner का installed Gradle उपयोग करता है।
- यह debug APK है, Play Store release APK नहीं।
- ऐप का backend अभी अलग से चलाना/host करना होगा। APK अकेले AI story/image/voice/video generation नहीं कर सकता।
- Backend server में OpenAI API key रखें; Android APK में API key कभी न डालें।
- Backend को public internet पर चलाने से पहले HTTPS, authentication और rate limiting लगाएँ।
- GitHub mobile UI में folder upload कठिन हो सकता है; जरूरत हो तो GitHub app/browser desktop mode उपयोग करें।
