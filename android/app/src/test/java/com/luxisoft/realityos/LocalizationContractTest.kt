package com.luxisoft.realityos

import android.app.Application
import java.io.File
import java.net.HttpURLConnection
import java.time.ZoneId
import java.util.Locale
import javax.xml.parsers.DocumentBuilderFactory
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.annotation.Config
import org.w3c.dom.Element

@RunWith(RobolectricTestRunner::class)
@Config(sdk = [35], application = Application::class)
class LocalizationContractTest {
    private val originalConnection = SocialSession.openJsonConnection
    private val originalLocale = Locale.getDefault()
    private val originalAccountLanguage = AccountRequestLanguage.value
    private lateinit var experience: RealityExperienceStore

    @Before fun prepare() {
        val context = RuntimeEnvironment.getApplication()
        LocalizedText.initialize(context)
        experience = RealityExperienceStore(context)
        experience.setLanguage(RealityLanguage.SPANISH)
        SocialSession.clear()
    }

    @After fun restore() {
        SocialSession.openJsonConnection = originalConnection
        SocialSession.clear()
        experience.setLanguage(RealityLanguage.ENGLISH)
        AccountRequestLanguage.value = originalAccountLanguage
        Locale.setDefault(originalLocale)
    }

    @Test fun resourcesKeepTranslationPluralAndPlaceholderContracts() {
        fun catalog(directory: String): Map<String, Map<String, List<String>>> = buildMap {
            File("src/main/res/$directory").listFiles()!!.filter { it.extension == "xml" }.forEach { file ->
                val nodes = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(file).documentElement.childNodes
                for (index in 0 until nodes.length) {
                    val resource = nodes.item(index) as? Element ?: continue
                    if (resource.tagName !in setOf("string", "plurals", "string-array") || resource.getAttribute("translatable") == "false") continue
                    val key = resource.getAttribute("name")
                    val variants = if (resource.tagName == "string") {
                        mapOf("value" to resource.textContent)
                    } else {
                        buildMap {
                            val items = resource.getElementsByTagName("item")
                            for (itemIndex in 0 until items.length) {
                                val item = items.item(itemIndex) as Element
                                put(item.getAttribute("quantity").ifBlank { itemIndex.toString() }, item.textContent)
                            }
                        }
                    }
                    assertFalse("Duplicate resource: $key", containsKey(key))
                    put(key, variants.mapValues { (_, value) -> Regex("%([0-9]+\\$)?[sdf]").findAll(value).map { it.value }.sorted().toList() })
                }
            }
        }
        val english = catalog("values")
        val spanish = catalog("values-es")
        assertEquals("Resource names differ", english.keys, spanish.keys)
        english.forEach { (key, formats) ->
            val translated = spanish.getValue(key)
            // CLDR quantities vary by language; Spanish also has `many`.
            // Extra quantities must preserve the fallback format arguments.
            (formats.keys + translated.keys).forEach { quantity ->
                assertEquals("Placeholders differ for $key/$quantity", formats[quantity] ?: formats["other"], translated[quantity] ?: translated["other"])
            }
        }
    }

    @Test fun selectedLanguageTravelsWithLoginRefreshFilesDownloadsAndDeviceRequests() {
        val server = MockWebServer().apply { start() }
        val video = File.createTempFile("localized-upload", ".mp4")
        try {
            SocialSession.openJsonConnection = { path -> server.url("/$path").toUrl().openConnection() as HttpURLConnection }
            server.enqueue(MockResponse().setBody("{}"))
            SocialSession.request("auth/login", JSONObject().put("email", "person@example.test"))
            assertEquals("es", server.takeRequest().getHeader("Accept-Language"))
            SocialSession.remember(JSONObject().put("access_token", "old-human").put("refresh_token", "refresh-human"))
            server.enqueue(MockResponse().setResponseCode(401))
            server.enqueue(MockResponse().setBody("""{"access_token":"new-human","refresh_token":"next-refresh"}"""))
            server.enqueue(MockResponse().setBody("{}"))
            SocialSession.request("me/profile")
            repeat(3) { assertEquals("es", server.takeRequest().getHeader("Accept-Language")) }
            val originalBytes = "original media bytes".toByteArray()
            server.enqueue(MockResponse().setBody("{}"))
            SocialSession.requestMultipart("me/publication-uploads", emptyMap(), originalBytes, "photo.png", "image/png")
            val photoRequest = server.takeRequest()
            assertEquals("es", photoRequest.getHeader("Accept-Language"))
            assertEquals("Bearer new-human", photoRequest.getHeader("Authorization"))
            assertTrue(photoRequest.body.readUtf8().contains(String(originalBytes)))
            video.writeBytes(originalBytes)
            server.enqueue(MockResponse().setBody("{}"))
            SocialSession.requestMultipartFile("me/publication-uploads", emptyMap(), video, "video/mp4")
            assertEquals("es", server.takeRequest().getHeader("Accept-Language"))
            server.enqueue(MockResponse().setBody("media"))
            assertEquals("media", String(SocialSession.download("media/1", SocialSession.identity, 32)))
            assertEquals("es", server.takeRequest().getHeader("Accept-Language"))
            experience.setLanguage(RealityLanguage.ENGLISH)
            server.enqueue(MockResponse().setBody("[]"))
            RealityApi(DeviceProvisioning(server.url("/").toString(), "workspace", "device-id", "device-key")).listZones()
            val deviceRequest = server.takeRequest()
            assertEquals("en", deviceRequest.getHeader("Accept-Language"))
            assertEquals("device-key", deviceRequest.getHeader("X-RealityOS-Device-Key"))
            assertNull(deviceRequest.getHeader("Authorization"))
        } finally {
            video.delete()
            server.shutdown()
        }
    }

    @Test fun authoredProfileDisplayAndDatesFollowAppLanguageWithoutRewritingEdits() {
        Locale.setDefault(Locale.JAPAN)
        val profile = JSONObject().put("display_name", "José Muñoz").put("gender", "Hombre").put("hometown", "Cusco, Perú")
            .put("display_text", JSONObject().put("gender", JSONObject().put("en", "Man").put("es", "Hombre")).put("hometown", JSONObject().put("en", "Cusco, Peru")))
        val raw = PersonalProfileDraft.from(profile)
        val english = PersonalProfileDraft.from(profile, "en")
        assertEquals("Hombre", raw.gender)
        assertEquals("Cusco, Perú", raw.addTo(JSONObject()).getString("hometown"))
        assertEquals("Man", english.gender)
        assertEquals("Cusco, Peru", english.hometown)
        assertEquals("José Muñoz", english.displayName)
        assertTrue(profileBirthdayLabel("1990-01-02", "es").contains("ene"))
        assertTrue(profileBirthdayLabel("1990-01-02", "en").contains("Jan"))
        val event = presentationDateTime("2026-11-04T19:45:00Z", "es", ZoneId.of("UTC"))
        assertTrue(event.contains("19:45"))
        assertEquals("invalid", presentationDateTime("invalid", "en"))
    }

    @Test fun pluralSelectionAndPreviewStatusResolveAgainAfterLanguageChanges() {
        Locale.setDefault(Locale.JAPAN)
        val state = DeveloperPreviewState(messageResource = R.string.debug_permission_denied, messageArguments = listOf(R.string.permission_camera))
        fun status() = localizedText(state.messageResource, *state.messageArguments.map { localizedText(it) }.toTypedArray())
        assertTrue(status().contains("denegado"))
        assertEquals("1 año", profileAgeLabel("1"))
        assertEquals("2 años", profileAgeLabel("2"))
        assertEquals("1000000 años", profileAgeLabel("1000000"))
        assertEquals("18–25 años", profileAgeLabel("18–25"))
        assertEquals("Encontré 1 persona: José", localizedQuantityText(R.plurals.chat_face_found, 1, 1, "José"))
        assertEquals("Encontré 2 personas: José, Ana", localizedQuantityText(R.plurals.chat_face_found, 2, 2, "José, Ana"))
        experience.setLanguage(RealityLanguage.ENGLISH)
        assertTrue(status().contains("denied"))
        assertEquals("1 year old", profileAgeLabel("1"))
        assertEquals("2 years old", profileAgeLabel("2"))
        assertEquals("", profileAgeLabel(""))
        assertEquals("I found 1 person: José", localizedQuantityText(R.plurals.chat_face_found, 1, 1, "José"))
        assertEquals("I found 2 people: José, Ana", localizedQuantityText(R.plurals.chat_face_found, 2, 2, "José, Ana"))
    }

    @Test fun networkAndMalformedResponsesDoNotExposeEnglishDiagnostics() {
        assertEquals(localizedText(R.string.account_network_error), localizedFailure(java.net.SocketTimeoutException("Read timed out")))
        assertEquals(localizedText(R.string.account_service_unavailable), localizedFailure(org.json.JSONException("Expected object")))
        assertEquals(localizedText(R.string.publish_needs_group), localizedFailure(IllegalArgumentException(localizedText(R.string.publish_needs_group))))
        assertEquals(localizedHttpError(403), localizedFailure(RealityApiException("HTTP response code 403", 403)))
    }

    @Test fun translatedPublicationErrorsRetainTheCorrectAction() {
        mapOf(
            "Únete a un grupo de trabajo o crea uno antes de publicar." to R.string.publish_needs_group,
            "Elige un grupo de trabajo." to R.string.publish_needs_group,
            "Imagen no válida." to R.string.ui_could_not_read_the_image,
            "Selecciona como máximo 20 etiquetas." to R.string.catalog_required,
            "La categoría o las etiquetas no son válidas." to R.string.catalog_required
        ).forEach { (message, resource) ->
            val body = JSONObject().put("detail", message).toString()
            assertEquals(localizedText(resource), publicationUploadFailure("me/publication-uploads", 422, body))
        }
        assertNull(publicationUploadFailure("unrelated-route", 422, "{}"))
    }
}
