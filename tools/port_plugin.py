"""Genera src/Mod/SpanishLocalization.cs a partir del plugin ruso (ref-russian/).

Cambios mínimos y verificados (cada reemplazo debe aplicarse, si no falla):
  - nombres: namespace, clase, GUID/Harmony id, carpetas Spanish_UI/Spanish_Texts, sufijo _spa
  - "ya traducido": los chequeos de cirílico pasan a IsTranslated() (HashSet de textos españoles)
  - búsqueda de passages: primero objeto exacto (001_patricia_02), luego base, luego título
  - fuentes: reemplazo de fuentes/SDF desactivado por config (Font/EnableFontReplacement=false)
  - sin " km" -> " км" ni quitado de mayúsculas
Uso: python tools/port_plugin.py
"""
import os
import re
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "ref-russian", "src", "Mod")
DST = os.path.join(ROOT, "src", "Mod")


def sub(s, pattern, repl, count=1, regex=False):
    n = len(re.findall(pattern, s)) if regex else s.count(pattern)
    if n < count:
        raise SystemExit(f"no se encontró ({n}/{count}): {pattern[:80]!r}")
    return re.sub(pattern, repl, s) if regex else s.replace(pattern, repl)


def port_cs(s):
    s = sub(s, "NightCallRussian", "NightCallSpanish")
    s = sub(s, "RussianLocalization", "SpanishLocalization", count=10)
    s = sub(s, '"com.nightcall.russian", "Night Call Russian", "8.1.0"',
            '"com.nightcall.spanish", "Night Call Spanish", "1.0.5"')
    s = sub(s, 'new Harmony("com.nightcall.russian")', 'new Harmony("com.nightcall.spanish")')
    s = sub(s, "Night Call Russian Localization v8.1.0", "Night Call Spanish Localization v1.0.5")
    s = sub(s, '"Russian_UI"', '"Spanish_UI"', count=2)
    s = sub(s, '"Russian_Texts"', '"Spanish_Texts"', count=2)
    s = sub(s, '"Russian_Texts_backup"', '"Spanish_Texts_backup"')
    s = sub(s, '.Replace("_rus", "_eng")', '.Replace("_spa", "_eng")')
    s = sub(s, '.Replace("_rus", "")', '.Replace("_spa", "")', count=2)
    s = sub(s, '"*_rus.txt"', '"*_spa.txt"')
    s = sub(s, 'value = value.Replace(" km", " км");', "// (español: los km se muestran igual)")

    # --- "ya traducido": HashSet de salidas españolas en lugar de detectar cirílico ---
    s = sub(s, "internal static Dictionary<string, string> RuToEngSpeaker = new Dictionary<string, string>();",
            "internal static Dictionary<string, string> RuToEngSpeaker = new Dictionary<string, string>();\n"
            "        // Textos españoles conocidos: si un texto ya está acá, no se vuelve a traducir.\n"
            "        internal static HashSet<string> SpanishValues = new HashSet<string>();\n"
            "        internal static bool IsTranslated(string text)\n"
            "        {\n"
            "            return !string.IsNullOrEmpty(text) && SpanishValues.Contains(text.Trim());\n"
            "        }")
    s = sub(s, r"// Check if already contains Cyrillic\s*foreach \(char c in text\)\s*\{\s*if \(c >= 0x0400 && c <= 0x04FF\) return null;\s*\}",
            "if (IsTranslated(text)) return null;", regex=True)
    s = sub(s, r"foreach \(char ch in part\)\s*\{\s*if \(ch >= 0x0400 && ch <= 0x04FF\) \{ hasCyr = true; break; \}\s*\}",
            "hasCyr = IsTranslated(part);", regex=True)
    s = sub(s, "foreach (char c in value) { if (c >= 0x0400 && c <= 0x04FF) { hasCyr = true; break; } }",
            "hasCyr = IsTranslated(value) || SpanishValues.Contains(value);")
    # El juego muestra ciertos textos en MAYÚSCULAS: en español se conserva ese estilo.
    s = sub(s, "// Check if translated text contains Cyrillic",
            "return; // español: se conserva el estilo en mayúsculas del juego\n#pragma warning disable CS0162")

    # --- construir SpanishValues después de cargar todo ---
    s = sub(s, "                Log.LogInfo(\"Loading passage dump for sequential fallback...\");",
            "                BuildSpanishValues();\n"
            "                Log.LogInfo(\"Loading passage dump for sequential fallback...\");")
    s = sub(s, "        void LoadDialogueTexts()",
            "        void BuildSpanishValues()\n"
            "        {\n"
            "            foreach (var v in Translations.Values) if (!string.IsNullOrEmpty(v)) SpanishValues.Add(v.Trim());\n"
            "            foreach (var v in KeyTranslations.Values) if (!string.IsNullOrEmpty(v)) SpanishValues.Add(v.Trim());\n"
            "            foreach (var lines in RussianPassages.Values)\n"
            "                foreach (var l in lines)\n"
            "                {\n"
            "                    if (string.IsNullOrEmpty(l) || l.StartsWith(\"$$\")) continue;\n"
            "                    SpanishValues.Add(l.Trim());\n"
            "                    int colon = l.IndexOf(\": \");\n"
            "                    if (colon > 0) SpanishValues.Add(l.Substring(colon + 2).Trim());\n"
            "                }\n"
            "            foreach (var chs in RussianChoices.Values)\n"
            "                foreach (var c in chs) if (c != null && c.Length > 0) SpanishValues.Add(c[0].Trim());\n"
            "            Log.LogInfo(string.Format(\"Spanish values (anti doble traducción): {0}\", SpanishValues.Count));\n"
            "        }\n\n"
            "        void LoadDialogueTexts()")

    # --- passages: primero el objeto exacto ---
    s = sub(s, 'RussianPassages.TryGetValue(objBase + ":" + passageTitle, out russianLines);',
            'RussianPassages.TryGetValue(objName + ":" + passageTitle, out russianLines);\n'
            '                        if (russianLines == null)\n'
            '                            RussianPassages.TryGetValue(objBase + ":" + passageTitle, out russianLines);')
    s = sub(s, 'RussianChoices.TryGetValue(objBase + ":" + passageTitle, out ruChoices);',
            'RussianChoices.TryGetValue(objName + ":" + passageTitle, out ruChoices);\n'
            '                                    if (ruChoices == null)\n'
            '                                        RussianChoices.TryGetValue(objBase + ":" + passageTitle, out ruChoices);')

    # --- fuentes: desactivadas por defecto ---
    s = sub(s, "private static ConfigEntry<float> FontScaleConfig;",
            "private static ConfigEntry<float> FontScaleConfig;\n"
            "        internal static bool FontReplacement = false;")
    s = sub(s, 'FontScaleConfig = Config.Bind("Font", "FontScale", 1.15f,',
            'FontReplacement = Config.Bind("Font", "EnableFontReplacement", false,\n'
            '                "Reemplazar fuentes del juego (solo si faltan glifos como ñ ¿ ¡)").Value;\n'
            '            FontScaleConfig = Config.Bind("Font", "FontScale", 1.0f,')
    s = sub(s, "                LoadCyrillicFonts();", "                if (FontReplacement) LoadCyrillicFonts();")

    # --- interruptores por capa (diagnóstico: activar/desactivar sin recompilar) ---
    s = sub(s, "        internal static bool FontReplacement = false;",
            "        internal static bool FontReplacement = false;\n"
            "        internal static bool LayerDialogs = true, LayerTextAssets = true, LayerTMP = true, LayerUIKeys = true;")
    s = sub(s, "            FontScale = FontScaleConfig.Value;",
            "            FontScale = FontScaleConfig.Value;\n"
            '            LayerDialogs = Config.Bind("Layers", "DialogObjects", true, "Reemplazar diálogos compilados (Spanish_Texts)").Value;\n'
            '            LayerTextAssets = Config.Bind("Layers", "TextAssets", true, "Reemplazar guiones TextAsset (intro, radio, periódicos...)").Value;\n'
            '            LayerTMP = Config.Bind("Layers", "TMPFallback", true, "Traducir textos TextMeshPro sueltos por mapping").Value;\n'
            '            LayerUIKeys = Config.Bind("Layers", "UIKeys", true, "Traducir claves de LocalizationManager").Value;\n'
            '            Log.LogInfo(string.Format("Capas: dialogs={0} textassets={1} tmp={2} uikeys={3}", LayerDialogs, LayerTextAssets, LayerTMP, LayerUIKeys));')
    s = sub(s, "                ReplaceDialogueObjects();", "                if (LayerDialogs) ReplaceDialogueObjects();")
    s = sub(s, "                ReplaceTextAssetContents();", "                if (LayerTextAssets) ReplaceTextAssetContents();")
    s = sub(s, "                PatchTMPText();", "                if (LayerTMP) PatchTMPText();")
    s = sub(s, "                PatchLocalizationManager(HarmonyInstance);", "                if (LayerUIKeys) PatchLocalizationManager(HarmonyInstance);")
    # --- pantalla de aviso (splashscreen): cada idioma es un TMP propio con un LocalizedText
    #     cuya "clave" no existe; se reemplaza SOLO el texto de las líneas EN por el español,
    #     sin tocar tamaño/estilo, y se apaga su LocalizedText para que no lo pise ---
    s = sub(s, "            processedTextKeys.Clear();\n            StartCoroutine(TranslateSceneDelayed());",
            "            processedTextKeys.Clear();\n"
            "            StartCoroutine(TranslateSceneDelayed());\n"
            "            if (scene.name == \"splashscreen\") StartCoroutine(TranslateSplash());")
    s = sub(s, "        void BuildSpanishValues()",
            "        static readonly string[][] SplashLines = {\n"
            "            new[] { \"Text - Warning - EN\", \"UI.SPLASHSCREEN.WARNING\" },\n"
            "            new[] { \"Text - Mature Content - EN\", \"UI.SPLASHSCREEN.MATURE\" } };\n\n"
            "        IEnumerator TranslateSplash()\n"
            "        {\n"
            "            // dos pasadas: al cargar y un instante después (por si algo reescribe el texto)\n"
            "            for (int pass = 0; pass < 2; pass++)\n"
            "            {\n"
            "                yield return new WaitForSeconds(pass == 0 ? 0.05f : 0.5f);\n"
            "                try\n"
            "                {\n"
            "                    foreach (var comp in Resources.FindObjectsOfTypeAll<Component>())\n"
            "                    {\n"
            "                        if (comp == null || !comp.gameObject.scene.IsValid()) continue;\n"
            "                        foreach (var sl in SplashLines)\n"
            "                        {\n"
            "                            string es;\n"
            "                            if (comp.name != sl[0] || !KeyTranslations.TryGetValue(sl[1], out es)) continue;\n"
            "                            PropertyInfo textProp = comp.GetType().GetProperty(\"text\", BindingFlags.Public | BindingFlags.Instance);\n"
            "                            if (object.ReferenceEquals(textProp, null) || !textProp.CanWrite) continue;\n"
            "                            foreach (var b in comp.GetComponents<Behaviour>())\n"
            "                                if (b != null && b.GetType().FullName == \"NC.I18N.LocalizedText\") b.enabled = false;\n"
            "                            textProp.SetValue(comp, es, null);\n"
            "                        }\n"
            "                    }\n"
            "                }\n"
            "                catch (Exception e) { Log.LogWarning(\"TranslateSplash: \" + e.Message); }\n"
            "            }\n"
            "        }\n\n"
            "        void BuildSpanishValues()")

    # --- F5: recargar traducciones sin reiniciar el juego ---
    s = sub(s, "        private static Dictionary<string, string> TranslationsLower = null;",
            "        internal static Dictionary<string, string> TranslationsLower = null;")
    s = sub(s, "            // Scanner disabled - translation now happens in TMP_Text.text setter and LocalizationManager patch",
            "            // F5: recarga Spanish_UI/Spanish_Texts desde disco (usar tras tools/install.py).\n"
            "            // Los cambios se ven en las próximas líneas que muestre el juego.\n"
            "            if (Input.GetKeyDown(ReloadKey)) ReloadAll();")
    s = sub(s, "        void BuildSpanishValues()",
            "        void ReloadAll()\n"
            "        {\n"
            "            try\n"
            "            {\n"
            "                Translations.Clear(); KeyTranslations.Clear(); DialogueTexts.Clear();\n"
            "                RussianPassages.Clear(); RussianChoices.Clear(); GlobalLinkToChoiceTexts.Clear();\n"
            "                SpanishValues.Clear(); TranslationsLower = null; ReplacedDialogueIds.Clear();\n"
            "                LoadTranslations(); LoadDialogueTexts(); LoadKeyTranslations(); BuildSpanishValues();\n"
            "                if (LayerUIKeys && LocalizationPatched) TryInjectTranslations();\n"
            "                ReplaceTextAssetsInMemory();\n"
            "                processedTextKeys.Clear();\n"
            "                StartCoroutine(TranslateSceneDelayed());\n"
            "                Log.LogInfo(string.Format(\"[F5] Recargado: {0} textos, {1} claves, {2} passages\", Translations.Count, KeyTranslations.Count, RussianPassages.Count));\n"
            "            }\n"
            "            catch (Exception e) { Log.LogError(\"[F5] Error al recargar: \" + e); }\n"
            "        }\n\n"
            "        void BuildSpanishValues()")
    s = sub(s, "        internal static bool LayerDialogs = true, LayerTextAssets = true, LayerTMP = true, LayerUIKeys = true;",
            "        internal static bool LayerDialogs = true, LayerTextAssets = true, LayerTMP = true, LayerUIKeys = true;\n"
            "        internal static KeyCode ReloadKey = KeyCode.F5;")
    s = sub(s, '            LayerUIKeys = Config.Bind("Layers", "UIKeys", true, "Traducir claves de LocalizationManager").Value;',
            '            LayerUIKeys = Config.Bind("Layers", "UIKeys", true, "Traducir claves de LocalizationManager").Value;\n'
            '            ReloadKey = Config.Bind("Debug", "ReloadKey", KeyCode.F5, "Tecla para recargar traducciones").Value;')

    s = sub(s, "            string text;\n            if (DialogueTexts.TryGetValue(assetName, out text))",
            "            string text;\n            if (LayerTextAssets && DialogueTexts.TryGetValue(assetName, out text))")
    s = sub(s, "            EnumerateAndPatchAllFonts();", "            if (FontReplacement) EnumerateAndPatchAllFonts();")

    # --- surtidor: "50.0" con el tanque lleno no entra en su caja y se recorta ---
    s = sub(s, "            // Replace TextAssets in memory with Russian content\n            ReplaceTextAssetsInMemory();",
            "            if (!ScrollingTextPatched && !object.ReferenceEquals(HarmonyInstance, null))\n"
            "                PatchScrollingText(HarmonyInstance);\n\n"
            "            // Replace TextAssets in memory with Russian content\n            ReplaceTextAssetsInMemory();")
    s = sub(s, "        IEnumerator TranslateSceneDelayed()\n        {", SCROLLING_TEXT_FIT + "        IEnumerator TranslateSceneDelayed()\n        {")

    # --- aviso de actualización: descarga, cierra el juego, instala y lo vuelve a abrir ---
    s = sub(s, "using UnityEngine.SceneManagement;", "using UnityEngine.SceneManagement;\nusing UnityEngine.Networking;")
    s = sub(s, 'ReloadKey = Config.Bind("Debug", "ReloadKey", KeyCode.F5, "Tecla para recargar traducciones").Value;',
            'ReloadKey = Config.Bind("Debug", "ReloadKey", KeyCode.F5, "Tecla para recargar traducciones").Value;\n'
            '            CheckUpdates = Config.Bind("Actualizaciones", "BuscarActualizaciones", true, "Al abrir el juego, avisar si hay una versión nueva de la traducción").Value;\n'
            '            SkipVersionConfig = Config.Bind("Actualizaciones", "OmitirVersion", "", "Versión de la que no se vuelve a avisar (la completa el botón \'No avisar de esta versión\')");')
    s = sub(s, "            IsInitialized = true;\n",
            "            IsInitialized = true;\n            StartCoroutine(CheckForUpdate());\n")
    s = sub(s, "        void OnDestroy()", UPDATER + "        void OnDestroy()")
    return s


UPDATER = r'''        // ===== Actualizaciones =====
        // Al abrir el juego consulta la última versión publicada en GitHub. Si es más nueva,
        // pregunta; con "Sí" descarga el zip del release (verifica su SHA-256), saca el
        // instalador, cierra el juego y un script espera a que termine de cerrarse, instala en
        // silencio sobre la misma carpeta y vuelve a abrir el juego. Las partidas no se tocan.
        // Mono del juego es .NET 3.5: la descarga va por UnityWebRequest (HttpWebRequest no
        // soporta el TLS de GitHub) y nada de APIs de .NET 4.
        const string UpdateApiUrl = "https://api.github.com/repos/maxeryt15/Nightcall-mod-spanish/releases/latest";
        const string UpdatePageUrl = "https://github.com/maxeryt15/Nightcall-mod-spanish/releases/latest";
        internal static bool CheckUpdates = true;
        private static ConfigEntry<string> SkipVersionConfig;
        private int updateState = 0; // 0 nada, 1 pregunta, 2 descargando, 3 error, 4 instalando
        private string updateVersion = "", updateNotes = "", updateUrl = "", updateDigest = "", updateError = "";
        private bool updateUrlIsZip = false;
        private float updateProgress = 0f;
        private GUIStyle updTitle, updText, updButton;
        // Pasar siempre las opciones: sin ellas el compilador usa Array.Empty (no existe en el Mono del juego)
        static readonly GUILayoutOption[] NoOpt = new GUILayoutOption[0];
        private Texture2D updPanel, updShade;
        private bool updPrevCursorVisible = true;
        private CursorLockMode updPrevCursorLock = CursorLockMode.None;

        IEnumerator CheckForUpdate()
        {
            if (!CheckUpdates) yield break;
            yield return new WaitForSeconds(3f);
            UnityWebRequest req = UnityWebRequest.Get(UpdateApiUrl);
            req.timeout = 15;
            yield return req.SendWebRequest();
            bool show = false;
            try
            {
                if (req.isNetworkError || req.isHttpError)
                    Log.LogInfo("[Update] No se pudo consultar: " + req.error);
                else
                    show = ParseUpdateInfo(req.downloadHandler.text);
            }
            catch (Exception e) { Log.LogWarning("[Update] " + e.Message); }
            req.Dispose();
            if (show)
            {
                Log.LogInfo("[Update] Versión nueva disponible: " + updateVersion);
                updPrevCursorVisible = Cursor.visible;
                updPrevCursorLock = Cursor.lockState;
                updateState = 1;
            }
        }

        bool ParseUpdateInfo(string json)
        {
            string tag = JsonStringValue(json, "tag_name", 0);
            if (string.IsNullOrEmpty(tag)) return false;
            Version latest = new Version(tag.TrimStart('v', 'V'));
            Version current = Info.Metadata.Version;
            Log.LogInfo(string.Format("[Update] Instalada v{0}, publicada v{1}", current, latest));
            if (latest.CompareTo(current) <= 0) return false;
            if (SkipVersionConfig.Value == latest.ToString()) return false;

            // Preferir un Setup.exe suelto; si no, el zip (lo que se publica hoy)
            string setupUrl = null, setupDigest = null, zipUrl = null, zipDigest = null;
            int prev = json.IndexOf("\"assets\"");
            if (prev < 0) return false;
            while (true)
            {
                int at = json.IndexOf("\"browser_download_url\"", prev + 1);
                if (at < 0) break;
                string url = JsonStringValue(json, "browser_download_url", at);
                string digest = null;
                int d = json.IndexOf("\"digest\"", prev + 1);
                if (d >= 0 && d < at) digest = JsonStringValue(json, "digest", d);
                if (digest != null && digest.StartsWith("sha256:")) digest = digest.Substring(7); else digest = null;
                if (url != null)
                {
                    if (url.EndsWith("_Setup.exe", StringComparison.OrdinalIgnoreCase)) { setupUrl = url; setupDigest = digest; }
                    else if (url.EndsWith(".zip", StringComparison.OrdinalIgnoreCase) && zipUrl == null) { zipUrl = url; zipDigest = digest; }
                }
                prev = at;
            }
            if (setupUrl != null) { updateUrl = setupUrl; updateDigest = setupDigest; updateUrlIsZip = false; }
            else if (zipUrl != null) { updateUrl = zipUrl; updateDigest = zipDigest; updateUrlIsZip = true; }
            else return false;

            updateVersion = latest.ToString();
            StringBuilder notes = new StringBuilder();
            string body = JsonStringValue(json, "body", 0) ?? "";
            int lines = 0;
            foreach (string raw in body.Split('\n'))
            {
                string line = raw.Replace("**", "").Trim();
                if (line.Length == 0 || line.StartsWith("#") || line.StartsWith("Para actualizar")) continue;
                if (lines++ >= 6) { notes.Append("..."); break; }
                notes.Append(line).Append('\n');
            }
            updateNotes = notes.ToString().TrimEnd(new char[] { (char)10, (char)13, ' ' });
            return true;
        }

        static string JsonStringValue(string json, string key, int start)
        {
            int k = json.IndexOf("\"" + key + "\"", start);
            if (k < 0) return null;
            int i = k + key.Length + 2;
            while (i < json.Length && (json[i] == ' ' || json[i] == ':' || json[i] == '\t' || json[i] == '\r' || json[i] == '\n')) i++;
            if (i >= json.Length || json[i] != '"') return null;
            StringBuilder sb = new StringBuilder();
            for (i++; i < json.Length; i++)
            {
                char c = json[i];
                if (c == '"') return sb.ToString();
                if (c != '\\' || i + 1 >= json.Length) { sb.Append(c); continue; }
                char e = json[++i];
                if (e == 'n') sb.Append('\n');
                else if (e == 't') sb.Append('\t');
                else if (e == 'r') { }
                else if (e == 'u' && i + 4 < json.Length) { sb.Append((char)Convert.ToInt32(json.Substring(i + 1, 4), 16)); i += 4; }
                else sb.Append(e);
            }
            return null;
        }

        IEnumerator DownloadAndInstall()
        {
            updateState = 2;
            updateProgress = 0f;
            UnityWebRequest req = UnityWebRequest.Get(updateUrl);
            req.SendWebRequest();
            while (!req.isDone)
            {
                if (updateState != 2) { req.Abort(); req.Dispose(); yield break; } // cancelado
                updateProgress = req.downloadProgress;
                yield return null;
            }
            string err;
            if (req.isNetworkError || req.isHttpError)
                err = "No se pudo descargar la actualización (" + req.error + ").";
            else
                err = InstallDownloaded(req.downloadHandler.data);
            req.Dispose();
            if (err != null)
            {
                Log.LogWarning("[Update] " + err);
                updateError = err;
                updateState = 3;
                yield break;
            }
            updateState = 4;
            yield return new WaitForSeconds(1.5f);
            Application.Quit();
        }

        // Devuelve null si todo salió bien, o el mensaje de error para mostrar.
        string InstallDownloaded(byte[] data)
        {
            try
            {
                if (!string.IsNullOrEmpty(updateDigest))
                {
                    string hash = BitConverter.ToString(new System.Security.Cryptography.SHA256Managed().ComputeHash(data)).Replace("-", "").ToLowerInvariant();
                    if (hash != updateDigest.ToLowerInvariant())
                        return "El archivo descargado llegó dañado. Intenta de nuevo más tarde.";
                }
                byte[] setup = updateUrlIsZip ? ExtractFromZip(data, "_Setup.exe") : data;
                if (setup == null || setup.Length < 2 || setup[0] != 'M' || setup[1] != 'Z')
                    return "La descarga no contiene el instalador.";

                string dir = Path.Combine(Path.GetTempPath(), "NightCallEspanol_Update");
                Directory.CreateDirectory(dir);
                string exe = Path.Combine(dir, "NightCallEspanol_Setup.exe");
                File.WriteAllBytes(exe, setup);
                string game = Paths.GameRootPath.Replace('/', '\\').TrimEnd('\\');
                string gameExe = Paths.ExecutablePath.Replace('/', '\\');
                int pid = System.Diagnostics.Process.GetCurrentProcess().Id;

                bool steam = game.ToLowerInvariant().Contains("\\steamapps\\");
                string script = Path.Combine(dir, "actualizar.ps1");
                string text = UpdateScript
                    .Replace("__PID__", pid.ToString())
                    .Replace("__VERSION__", updateVersion)
                    .Replace("__STEAM__", steam ? "$true" : "$false")
                    .Replace("__SETUP__", PsQuote(exe))
                    .Replace("__GAME__", PsQuote(game))
                    .Replace("__GAMEEXE__", PsQuote(gameExe))
                    .Replace("__PROCNAME__", PsQuote(Path.GetFileNameWithoutExtension(gameExe)))
                    .Replace("__INSTLOG__", PsQuote(Path.Combine(dir, "instalacion.log")))
                    .Replace("__LOG__", PsQuote(Path.Combine(dir, "actualizacion.log")));
                File.WriteAllText(script, text, new UTF8Encoding(true)); // con BOM: PowerShell 5 lee bien acentos/ñ

                // El actualizador NO puede ser hijo del juego: Steam da el juego por abierto mientras
                // viva cualquier proceso que el juego lanzó, y el script se quedaba esperando a Steam
                // para siempre. lanzar.ps1 lo crea vía WMI (proceso independiente) y termina enseguida.
                string launcher = Path.Combine(dir, "lanzar.ps1");
                File.WriteAllText(launcher, LaunchScript.Replace("__SCRIPT__", PsQuote(script)), new UTF8Encoding(true));

                System.Diagnostics.ProcessStartInfo psi = new System.Diagnostics.ProcessStartInfo("powershell.exe",
                    "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \"" + launcher + "\"");
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;
                psi.WorkingDirectory = dir;
                System.Diagnostics.Process.Start(psi);
                Log.LogInfo("[Update] Instalador listo, cerrando el juego: " + exe);
                return null;
            }
            catch (Exception e)
            {
                Log.LogWarning("[Update] " + e);
                return "No se pudo preparar la instalación (" + e.Message + ").";
            }
        }

        static string PsQuote(string s) { return s.Replace("'", "''"); }

        const string LaunchScript = @"$linea = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""__SCRIPT__""'
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $linea }
if (-not $r -or $r.ReturnValue -ne 0) {
    # Sin WMI: lanzarlo igual (Steam puede tardar en soltar el juego, el script tiene tope)
    Start-Process powershell.exe -ArgumentList '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""__SCRIPT__""' -WindowStyle Hidden
}
";

        // Corre fuera del juego (PowerShell oculto + ventana de Windows con el estado):
        // 1) cierra el juego a la fuerza enseguida (no espera a que se cierre solo)
        // 2) instala en silencio
        // 3) en Steam, espera a que Steam dé el juego por cerrado (si no: "Game already running";
        //    Steam lo retiene mientras sincroniza la nube) y lo abre como el botón Jugar (el .exe
        //    suelto se cierra y le pide a Steam que lo abra); fuera de Steam, el .exe desde su
        //    carpeta (doorstop busca BepInEx con ruta relativa)
        // 4) se cierra sola cuando el juego ya está abierto. Deja la hora de cada paso en actualizacion.log.
        const string UpdateScript = @"$ErrorActionPreference = 'SilentlyContinue'
$log = '__LOG__'
function Anotar($t) { Add-Content -LiteralPath $log -Value ((Get-Date).ToString('HH:mm:ss') + '  ' + $t) -Encoding UTF8 }
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[Windows.Forms.Application]::EnableVisualStyles()
$form = New-Object Windows.Forms.Form
$form.Text = 'Night Call - Traducción al español'
$form.ClientSize = New-Object Drawing.Size(480, 132)
$form.StartPosition = 'CenterScreen'
$form.FormBorderStyle = 'FixedDialog'
$form.ControlBox = $false
$form.TopMost = $true
$form.BackColor = [Drawing.Color]::FromArgb(20, 20, 22)
$titulo = New-Object Windows.Forms.Label
$titulo.Text = 'Actualizando a la v__VERSION__'
$titulo.ForeColor = [Drawing.Color]::FromArgb(219, 186, 99)
$titulo.Font = New-Object Drawing.Font('Segoe UI', 12, [Drawing.FontStyle]::Bold)
$titulo.SetBounds(20, 14, 440, 26)
$estado = New-Object Windows.Forms.Label
$estado.ForeColor = [Drawing.Color]::White
$estado.Font = New-Object Drawing.Font('Segoe UI', 10)
$estado.SetBounds(20, 44, 440, 44)
$barra = New-Object Windows.Forms.ProgressBar
$barra.Style = 'Marquee'
$barra.MarqueeAnimationSpeed = 30
$barra.SetBounds(20, 98, 440, 16)
$form.Controls.Add($titulo); $form.Controls.Add($estado); $form.Controls.Add($barra)
$form.Show()
function Pausa($ms) { $fin = (Get-Date).AddMilliseconds($ms); do { [Windows.Forms.Application]::DoEvents(); Start-Sleep -Milliseconds 50 } while ((Get-Date) -lt $fin) }
function Estado($t) { $estado.Text = $t; Anotar $t; Pausa 100 }

Estado 'Cerrando el juego...'
$juego = Get-Process -Id __PID__
if ($juego -and -not $juego.HasExited) {
    # Sin esperar: la descarga ya terminó y el juego está en el menú, no hay nada que guardar
    Stop-Process -Id __PID__ -Force
    $tope = (Get-Date).AddSeconds(10)
    while (-not $juego.HasExited -and (Get-Date) -lt $tope) { Pausa 100 }
}

Estado 'Instalando la traducción...'
$inst = Start-Process -FilePath '__SETUP__' -ArgumentList '/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP- ""/DIR=__GAME__"" ""/LOG=__INSTLOG__""' -PassThru
while (-not $inst.HasExited) { Pausa 200 }
if ($inst.ExitCode -ne 0) {
    Estado ('No se pudo instalar (código ' + $inst.ExitCode + '). Vuelve a intentarlo desde el juego.')
    Pausa 10000
    exit
}

if (__STEAM__) {
    Estado 'Actualización instalada. Esperando a que Steam termine de cerrar el juego (Steam está sincronizando, puede tardar un poco)...'
    $tope = (Get-Date).AddSeconds(45)
    while ((Get-ItemProperty -Path 'HKCU:\Software\Valve\Steam\Apps\680380').Running -eq 1 -and (Get-Date) -lt $tope) { Pausa 200 }
    Estado 'Abriendo Night Call desde Steam...'
    Pausa 1000
    Start-Process 'steam://rungameid/680380'
} else {
    Estado 'Abriendo Night Call...'
    Start-Process -FilePath '__GAMEEXE__' -WorkingDirectory '__GAME__'
}
$n = 0
while (-not (Get-Process -Name '__PROCNAME__') -and $n -lt 120) { Pausa 500; $n++ }
Estado 'Listo. ¡A manejar!'
Pausa 1500
$form.Close()
";

        // Lector mínimo de zip (el Mono del juego no trae ZipArchive): busca la entrada
        // cuyo nombre termina en `suffix` y la descomprime con DeflateStream.
        static byte[] ExtractFromZip(byte[] zip, string suffix)
        {
            int eocd = -1;
            for (int i = zip.Length - 22; i >= Math.Max(0, zip.Length - 65557); i--)
                if (BitConverter.ToUInt32(zip, i) == 0x06054b50) { eocd = i; break; }
            if (eocd < 0) return null;
            int count = BitConverter.ToUInt16(zip, eocd + 10);
            int p = (int)BitConverter.ToUInt32(zip, eocd + 16);
            for (int n = 0; n < count; n++)
            {
                if (BitConverter.ToUInt32(zip, p) != 0x02014b50) return null;
                int method = BitConverter.ToUInt16(zip, p + 10);
                int csize = (int)BitConverter.ToUInt32(zip, p + 20);
                int usize = (int)BitConverter.ToUInt32(zip, p + 24);
                int nlen = BitConverter.ToUInt16(zip, p + 28);
                int skip = nlen + BitConverter.ToUInt16(zip, p + 30) + BitConverter.ToUInt16(zip, p + 32);
                int local = (int)BitConverter.ToUInt32(zip, p + 42);
                string name = Encoding.UTF8.GetString(zip, p + 46, nlen);
                p += 46 + skip;
                if (!name.EndsWith(suffix, StringComparison.OrdinalIgnoreCase)) continue;
                int data = local + 30 + BitConverter.ToUInt16(zip, local + 26) + BitConverter.ToUInt16(zip, local + 28);
                byte[] result = new byte[usize];
                if (method == 0) { Buffer.BlockCopy(zip, data, result, 0, usize); return result; }
                if (method != 8) return null;
                using (var ds = new System.IO.Compression.DeflateStream(new MemoryStream(zip, data, csize), System.IO.Compression.CompressionMode.Decompress))
                {
                    int read = 0;
                    while (read < usize)
                    {
                        int r = ds.Read(result, read, usize - read);
                        if (r <= 0) break;
                        read += r;
                    }
                    if (read != usize) return null;
                }
                return result;
            }
            return null;
        }

        void CloseUpdateWindow()
        {
            updateState = 0;
            Cursor.visible = updPrevCursorVisible;
            Cursor.lockState = updPrevCursorLock;
        }

        // Marca de versión en la esquina durante los primeros segundos del juego
        const float VersionBadgeSeconds = 15f;
        private GUIStyle badgeStyle;

        void OnGUI()
        {
            if (Time.realtimeSinceStartup < VersionBadgeSeconds)
            {
                try { DrawVersionBadge(); } catch { }
            }
            if (updateState == 0) return;
            try { DrawUpdateWindow(); }
            catch (Exception e) { Log.LogWarning("[Update] GUI: " + e.Message); CloseUpdateWindow(); }
        }

        void DrawVersionBadge()
        {
            if (badgeStyle == null)
            {
                badgeStyle = new GUIStyle(GUI.skin.label);
                badgeStyle.fontSize = 16;
                badgeStyle.fontStyle = FontStyle.Bold;
                badgeStyle.alignment = TextAnchor.LowerRight;
            }
            float scale = Screen.height / 720f;
            GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(scale, scale, 1f));
            float vw = Screen.width / scale;
            // se desvanece en los últimos 2 segundos
            float alpha = Mathf.Clamp01((VersionBadgeSeconds - Time.realtimeSinceStartup) / 2f);
            string text = "Night Call Spanish Mod v" + Info.Metadata.Version;
            Rect r = new Rect(vw - 420, 720 - 44, 400, 30);
            badgeStyle.normal.textColor = new Color(0f, 0f, 0f, 0.8f * alpha);
            GUI.Label(new Rect(r.x + 1.5f, r.y + 1.5f, r.width, r.height), text, badgeStyle);
            badgeStyle.normal.textColor = new Color(0.86f, 0.73f, 0.39f, alpha);
            GUI.Label(r, text, badgeStyle);
            GUI.matrix = Matrix4x4.identity;
        }

        void DrawUpdateWindow()
        {
            if (updTitle == null)
            {
                updTitle = new GUIStyle(GUI.skin.label);
                updTitle.fontSize = 24; updTitle.fontStyle = FontStyle.Bold; updTitle.wordWrap = true;
                updTitle.normal.textColor = new Color(0.86f, 0.73f, 0.39f);
                updText = new GUIStyle(GUI.skin.label);
                updText.fontSize = 16; updText.wordWrap = true; updText.normal.textColor = Color.white;
                updButton = new GUIStyle(GUI.skin.button);
                updButton.fontSize = 16; updButton.padding = new RectOffset(12, 12, 8, 8);
                updPanel = new Texture2D(1, 1); updPanel.SetPixel(0, 0, new Color(0.06f, 0.06f, 0.07f, 0.97f)); updPanel.Apply();
                updShade = new Texture2D(1, 1); updShade.SetPixel(0, 0, new Color(0f, 0f, 0f, 0.6f)); updShade.Apply();
            }
            Cursor.visible = true;
            Cursor.lockState = CursorLockMode.None;
            GUI.depth = -1000;

            // Coordenadas virtuales de 720 de alto, escaladas a la resolución real
            float scale = Screen.height / 720f;
            GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(scale, scale, 1f));
            float vw = Screen.width / scale;
            GUI.DrawTexture(new Rect(0, 0, vw, 720), updShade);
            float w = 620, h = updateState == 1 ? 400 : 220;
            Rect box = new Rect((vw - w) / 2f, (720 - h) / 2f, w, h);
            GUI.DrawTexture(box, updPanel);

            GUILayout.BeginArea(new Rect(box.x + 28, box.y + 24, w - 56, h - 48));
            if (updateState == 1)
            {
                GUILayout.Label("Nueva versión de la traducción", updTitle, NoOpt);
                GUILayout.Space(8);
                GUILayout.Label(string.Format("Hay una actualización disponible: v{0} (tienes v{1}).", updateVersion, Info.Metadata.Version), updText, NoOpt);
                if (updateNotes.Length > 0) { GUILayout.Space(6); GUILayout.Label(updateNotes, updText, NoOpt); }
                GUILayout.FlexibleSpace();
                GUILayout.Label("Si aceptas, el juego se cerrará, se instalará la actualización y se volverá a abrir solo. Tus partidas guardadas no se tocan.", updText, NoOpt);
                GUILayout.Space(12);
                GUILayout.BeginHorizontal(NoOpt);
                if (GUILayout.Button("Sí, actualizar ahora", updButton, NoOpt)) StartCoroutine(DownloadAndInstall());
                if (GUILayout.Button("Ahora no", updButton, NoOpt)) CloseUpdateWindow();
                if (GUILayout.Button("No avisar de esta versión", updButton, NoOpt))
                {
                    SkipVersionConfig.Value = updateVersion;
                    CloseUpdateWindow();
                }
                GUILayout.EndHorizontal();
            }
            else if (updateState == 2)
            {
                GUILayout.Label("Descargando actualización...", updTitle, NoOpt);
                GUILayout.Space(12);
                GUILayout.Label(string.Format("v{0}: {1}%", updateVersion, Mathf.RoundToInt(updateProgress * 100f)), updText, NoOpt);
                GUILayout.FlexibleSpace();
                if (GUILayout.Button("Cancelar", updButton, NoOpt)) CloseUpdateWindow();
            }
            else if (updateState == 3)
            {
                GUILayout.Label("No se pudo actualizar", updTitle, NoOpt);
                GUILayout.Space(8);
                GUILayout.Label(updateError + " Puedes descargarla a mano desde la página del mod.", updText, NoOpt);
                GUILayout.FlexibleSpace();
                GUILayout.BeginHorizontal(NoOpt);
                if (GUILayout.Button("Abrir página de descarga", updButton, NoOpt)) { Application.OpenURL(UpdatePageUrl); CloseUpdateWindow(); }
                if (GUILayout.Button("Cerrar", updButton, NoOpt)) CloseUpdateWindow();
                GUILayout.EndHorizontal();
            }
            else
            {
                GUILayout.Label("Actualización descargada", updTitle, NoOpt);
                GUILayout.Space(8);
                GUILayout.Label("Cerrando el juego para instalarla. Se volverá a abrir en unos segundos.", updText, NoOpt);
            }
            GUILayout.EndArea();
            GUI.matrix = Matrix4x4.identity;
        }

'''


SCROLLING_TEXT_FIT = r'''        // Contadores que "ruedan" (surtidor: volumen y precio). El juego los dibuja con un
        // tamaño fijo y "50.0" con el tanque lleno se sale de la caja y queda recortado.
        // Best fit: mantiene el tamaño original y solo achica si el número no entra.
        private static bool ScrollingTextPatched = false;

        void PatchScrollingText(Harmony harmony)
        {
            ScrollingTextPatched = true;
            try
            {
                Type scrollType = null;
                foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
                {
                    scrollType = assembly.GetType("NC.UI.UIScrollingText");
                    if (!object.ReferenceEquals(scrollType, null)) break;
                }
                if (object.ReferenceEquals(scrollType, null))
                {
                    Log.LogWarning("UIScrollingText not found");
                    return;
                }

                MethodInfo awake = scrollType.GetMethod("Awake", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                MethodInfo postfix = typeof(SpanishLocalization).GetMethod("UIScrollingText_Awake_Postfix", BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Static);
                if (!object.ReferenceEquals(awake, null) && !object.ReferenceEquals(postfix, null))
                    harmony.Patch(awake, postfix: new HarmonyMethod(postfix));

                // Instancias que ya pasaron por Awake antes del parche
                foreach (var existing in Resources.FindObjectsOfTypeAll(scrollType))
                    UIScrollingText_Awake_Postfix(existing);

                Log.LogInfo("UIScrollingText patched (best fit)");
            }
            catch (Exception e)
            {
                Log.LogWarning(string.Format("UIScrollingText patch failed: {0}", e.Message));
            }
        }

        static void UIScrollingText_Awake_Postfix(object __instance)
        {
            try
            {
                Type t = __instance.GetType();
                foreach (string name in new string[] { "text", "text_up" })
                {
                    FieldInfo f = t.GetField(name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                    if (object.ReferenceEquals(f, null)) continue;
                    Text text = f.GetValue(__instance) as Text;
                    if (text == null || text.resizeTextForBestFit) continue;
                    int size = text.fontSize;
                    text.resizeTextMaxSize = size;
                    text.resizeTextMinSize = Math.Max(1, size / 2);
                    text.horizontalOverflow = HorizontalWrapMode.Wrap;
                    text.resizeTextForBestFit = true;
                }
            }
            catch (Exception e)
            {
                if (Log != null) Log.LogWarning(string.Format("[ScrollingText] {0}", e.Message));
            }
        }

'''


if __name__ == "__main__":
    os.makedirs(os.path.join(DST, "Properties"), exist_ok=True)
    with open(os.path.join(SRC, "RussianLocalization.cs"), encoding="utf-8-sig") as f:
        cs = port_cs(f.read())
    with open(os.path.join(DST, "SpanishLocalization.cs"), "w", encoding="utf-8", newline="\n") as f:
        f.write(cs)
    with open(os.path.join(SRC, "NightCallRussian.csproj"), encoding="utf-8-sig") as f:
        proj = f.read()
    proj = proj.replace("NightCallRussian", "NightCallSpanish")
    proj = proj.replace(r"$(MSBuildThisFileDirectory)..\..\libs", r"$(MSBuildThisFileDirectory)..\..\ref-russian\libs")
    proj = proj.replace(r"$(MSBuildThisFileDirectory)..\..\data\BepInEx\core", r"$(MSBuildThisFileDirectory)..\..\ref-russian\data\BepInEx\core")
    proj = proj.replace("<GenerateAssemblyInfo>false</GenerateAssemblyInfo>",
                        "<GenerateAssemblyInfo>false</GenerateAssemblyInfo>\n    <NoWarn>CS0162</NoWarn>")
    # Actualizador: UnityWebRequest (no viene en ref-russian/libs; se toma del juego instalado)
    proj = proj.replace("</PropertyGroup>",
                        "  <GameManagedDir Condition=\"'$(GameManagedDir)' == ''\">D:\\SteamLibrary\\steamapps\\common\\Night Call\\Night Call_Data\\Managed</GameManagedDir>\n"
                        "  </PropertyGroup>", 1)
    proj = proj.replace("  </ItemGroup>",
                        "    <Reference Include=\"UnityEngine.UnityWebRequestModule\">\n"
                        "      <HintPath>$(GameManagedDir)\\UnityEngine.UnityWebRequestModule.dll</HintPath>\n"
                        "      <Private>false</Private>\n"
                        "    </Reference>\n"
                        "  </ItemGroup>", 1)
    with open(os.path.join(DST, "NightCallSpanish.csproj"), "w", encoding="utf-8", newline="\n") as f:
        f.write(proj)
    # AssemblyInfo: nombres en español y la versión real (el ruso traía 6.1.0.0, que se veía
    # en Propiedades de la DLL). Mantener igual a la versión del BepInPlugin y del instalador.
    with open(os.path.join(SRC, "Properties", "AssemblyInfo.cs"), encoding="utf-8-sig") as f:
        info = f.read().replace("Russian", "Spanish")
    info = re.sub(r'(Assembly(?:File)?Version\(")[\d.]+("\))', r"\g<1>1.0.5.0\g<2>", info)
    with open(os.path.join(DST, "Properties", "AssemblyInfo.cs"), "w", encoding="utf-8", newline="\n") as f:
        f.write(info)
    print("port listo: src/Mod/SpanishLocalization.cs")
