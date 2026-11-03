import java.net.URI
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.util.Properties
import org.jetbrains.kotlin.gradle.dsl.JvmTarget

plugins {
  alias(libs.plugins.android.application)
  alias(libs.plugins.jetbrains.kotlin.android)
  alias(libs.plugins.compose.compiler)
}

val localProperties = Properties().apply {
  val file = rootDir.resolve("local.properties")
  if (file.exists()) file.inputStream().use(::load)
}

fun androidClientSetting(property: String, variable: String): String =
  localProperties.getProperty(property) ?: providers.environmentVariable(variable).getOrElse("0")
val facebookAppId = androidClientSetting("facebook_app_id", "ANDROID_FACEBOOK_APP_ID")
val facebookClientToken = androidClientSetting("facebook_client_token", "ANDROID_FACEBOOK_CLIENT_TOKEN")

val localDevelopment = providers.gradleProperty("localDevelopment").orElse("false").get().toBooleanStrict()
val configuredApiUrl = providers.environmentVariable("REALITYOS_API_BASE_URL")
  .orElse(providers.gradleProperty("realityosApiBaseUrl"))
val productionApiUrl = "https://realityos.luxisoft.com/v1"
val debugApiUrl = configuredApiUrl.getOrElse(if (localDevelopment) "http://localhost:8080/v1" else productionApiUrl)
val debugUri = URI(debugApiUrl)
require(debugUri.userInfo == null && debugUri.query == null && debugUri.fragment == null) { "Use a plain API base URL." }
require(if (localDevelopment) debugUri.scheme == "http" && debugUri.host in setOf("localhost", "127.0.0.1", "10.0.2.2") else debugUri.scheme == "https") {
  "Local development requires loopback HTTP; normal builds require HTTPS."
}

android {
  namespace = "com.luxisoft.realityos"
  compileSdk = 36

  defaultConfig {
    manifestPlaceholders["facebook_app_id"] = facebookAppId
    manifestPlaceholders["facebook_client_token"] = facebookClientToken
    buildConfigField("String", "FACEBOOK_APP_ID", "\"${facebookAppId}\"")
    applicationId = "com.luxisoft.realityos"
    minSdk = 31
    targetSdk = 36
    versionCode = 7
    versionName = "0.1.6"
    // Without this, AGP falls back to the legacy InstrumentationTestRunner,
    // which does not discover AndroidJUnit4 MockDeviceKit tests.
    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    manifestPlaceholders["mwdat_application_id"] =
      localProperties.getProperty("mwdat_application_id", "0")
    manifestPlaceholders["mwdat_client_token"] =
      localProperties.getProperty("mwdat_client_token", "0")
    // Public URL only. The live virtual-device credential is issued at runtime
    // over TLS and is never compiled into the APK.
    buildConfigField("boolean", "LOCAL_DEVELOPMENT", "false")
    buildConfigField("String", "DEFAULT_REALITYOS_API_BASE_URL", "\"${if (localDevelopment) productionApiUrl else debugApiUrl}\"")

  }

  buildFeatures { buildConfig = true }
  testOptions {
    unitTests.isIncludeAndroidResources = true
  }
  buildTypes {
    debug {
      buildConfigField("boolean", "LOCAL_DEVELOPMENT", localDevelopment.toString())
      buildConfigField("String", "DEFAULT_REALITYOS_API_BASE_URL", "\"$debugApiUrl\"")
      manifestPlaceholders["local_cleartext_allowed"] = localDevelopment.toString()
      manifestPlaceholders["debug_network_security_config"] = if (localDevelopment) "@xml/network_security_local" else "@xml/network_security_secure"
      if (localDevelopment) applicationIdSuffix = ".local"
      // Timestamped debug builds: the exact APK under test is visible in
      // Settings -> Apps, so stale installs are easy to spot.
      versionNameSuffix = "-debug-" + LocalDateTime.now()
        .format(DateTimeFormatter.ofPattern("yyyyMMdd-HHmm"))
    }
    release {
      isMinifyEnabled = false
      proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
    }
  }
  compileOptions {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
  }
}

kotlin { compilerOptions { jvmTarget = JvmTarget.JVM_17 } }

dependencies {
  implementation("com.facebook.android:facebook-login:18.1.3")
  implementation("com.adamglin:phosphor-icon:1.0.0")
  implementation("io.coil-kt:coil-compose:2.7.0")
  implementation(libs.androidx.activity.compose)
  implementation(platform(libs.androidx.compose.bom))
  implementation(libs.androidx.ui)
  implementation(libs.androidx.ui.graphics)
  implementation(libs.androidx.ui.tooling.preview)
  implementation(libs.androidx.material3)
  implementation(libs.androidx.lifecycle.runtime.compose)
  implementation(libs.androidx.lifecycle.viewmodel.compose)
  implementation(libs.androidx.security.crypto)
  implementation(libs.androidx.appcompat)
  implementation(libs.androidx.core.splashscreen)
  implementation(libs.androidx.material.icons.extended)
  implementation(libs.androidx.camera.core)
  implementation(libs.androidx.camera.camera2)
  implementation(libs.androidx.camera.lifecycle)
  implementation(libs.androidx.camera.video)
  implementation(libs.androidx.camera.view)
  implementation(libs.androidx.media3.exoplayer)
  implementation(libs.androidx.media3.ui)
  implementation(libs.mwdat.core)
  implementation(libs.mwdat.camera)
  implementation(libs.mwdat.display)
  implementation(libs.mwdat.speech)
  testImplementation("junit:junit:4.13.2")
  testImplementation("org.robolectric:robolectric:4.16.1")
  testImplementation("com.squareup.okhttp3:mockwebserver:4.12.0")
  testImplementation("com.squareup.okhttp3:okhttp-tls:4.12.0")
  testImplementation("androidx.compose.ui:ui-test-junit4")
  androidTestImplementation("androidx.test.ext:junit:1.2.1")
  androidTestImplementation("androidx.test:runner:1.6.2")
  androidTestImplementation("com.squareup.okhttp3:mockwebserver:4.12.0")
  androidTestImplementation("com.squareup.okhttp3:okhttp-tls:4.12.0")
  androidTestImplementation(platform(libs.androidx.compose.bom))
  androidTestImplementation("androidx.compose.ui:ui-test-junit4")
  // Debug builds expose Meta's Developer Preview on a phone. Release builds
  // never package Mock Device Kit.
  debugImplementation(libs.mwdat.mockdevice)
  // Instrumentation uses the same official kit independently of the app's
  // Debug source set.
  androidTestImplementation(libs.mwdat.mockdevice)
  debugImplementation("androidx.compose.ui:ui-tooling")
  debugImplementation("androidx.compose.ui:ui-test-manifest")
}

// Format the refactored host/chat code without rewriting protected biometric UI.
val ktlint by configurations.creating

dependencies {
    add(ktlint.name, "com.pinterest.ktlint:ktlint-cli:1.7.1")
}

val refactoredKotlin = files(
    "src/main/java/com/luxisoft/realityos/AccountForm.kt",
    "src/main/java/com/luxisoft/realityos/AccountField.kt",
    "src/main/java/com/luxisoft/realityos/AccountArtwork.kt",
    "src/main/java/com/luxisoft/realityos/AccountEntry.kt",
    "src/testDebug/java/com/luxisoft/realityos/AccountEntryTest.kt",
    "src/main/java/com/luxisoft/realityos/WorkspaceRecords.kt",
    "src/testDebug/java/com/luxisoft/realityos/WorkspaceRecordsTest.kt",
    "src/main/java/com/luxisoft/realityos/ProfileHeader.kt",
    "src/main/java/com/luxisoft/realityos/ProfileDetails.kt",
    "src/main/java/com/luxisoft/realityos/ProfileScreen.kt",
    "src/testDebug/java/com/luxisoft/realityos/ProfileHeaderTest.kt",
    "src/main/java/com/luxisoft/realityos/DisplayResultImages.kt",
    "src/test/java/com/luxisoft/realityos/DisplayResultImagesTest.kt",
    "src/main/java/com/luxisoft/realityos/DisplayProfileNavigation.kt",
    "src/test/java/com/luxisoft/realityos/DisplayProfileNavigationTest.kt",
    "src/androidTest/java/com/luxisoft/realityos/DisplaySearchCameraTest.kt",
    "src/main/java/com/luxisoft/realityos/LocalAccessPolicy.kt",
    "src/test/java/com/luxisoft/realityos/LocalAccessPolicyTest.kt",
    "src/debug/java/com/luxisoft/realityos/LocalAccountEntry.kt",
    "src/release/java/com/luxisoft/realityos/LocalAccountEntry.kt",
    "src/main/java/com/luxisoft/realityos/AgentSpeechPlayer.kt",
    "src/test/java/com/luxisoft/realityos/AgentSpeechPlayerTest.kt",
    "src/main/java/com/luxisoft/realityos/InputRoute.kt",
    "src/main/java/com/luxisoft/realityos/PhonePreviewState.kt",
    "src/main/java/com/luxisoft/realityos/PhoneInputSources.kt",
    "src/main/java/com/luxisoft/realityos/DeveloperPreview.kt",
    "src/test/java/com/luxisoft/realityos/InputRoutePolicyTest.kt",
    "src/test/java/com/luxisoft/realityos/PhonePreviewStateTest.kt",
    "src/debug/java/com/luxisoft/realityos/DeveloperPreviewPanel.kt",
    "src/debug/java/com/luxisoft/realityos/PhoneCaptureViewfinder.kt",
    "src/testDebug/java/com/luxisoft/realityos/PhoneCaptureTouchTest.kt",
    "src/debug/java/com/luxisoft/realityos/MockDeveloperPreviewController.kt",
    "src/main/java/com/luxisoft/realityos/MetaDisplayState.kt",
    "src/main/java/com/luxisoft/realityos/MetaDisplayController.kt",
    "src/main/java/com/luxisoft/realityos/MetaDisplayScreens.kt",
    "src/test/java/com/luxisoft/realityos/MetaDisplayPolicyTest.kt",
    "src/main/java/com/luxisoft/realityos/ChatLocalization.kt",
    "src/main/java/com/luxisoft/realityos/RealityExperienceStore.kt",
    "src/test/java/com/luxisoft/realityos/ChatLocalizationTest.kt",
    "src/main/java/com/luxisoft/realityos/EvidencePresentation.kt",
    "src/main/java/com/luxisoft/realityos/EvidenceInformation.kt",
    "src/test/java/com/luxisoft/realityos/EvidencePresentationTest.kt",
    "src/main/java/com/luxisoft/realityos/ChatAutoScroll.kt",
    "src/test/java/com/luxisoft/realityos/ChatScrollPolicyTest.kt",
    "src/test/java/com/luxisoft/realityos/ChatEvidenceTest.kt",
    "src/main/java/com/luxisoft/realityos/ChatEvidence.kt",
    "src/main/java/com/luxisoft/realityos/SearchEvidenceCarousel.kt",
    "src/main/java/com/luxisoft/realityos/PublicationUploader.kt",
    "src/test/java/com/luxisoft/realityos/GalleryViewerUrlTest.kt",
    "src/main/java/com/luxisoft/realityos/LoadingSkeleton.kt",
    "src/main/java/com/luxisoft/realityos/GalleryTopBarState.kt",
    "src/main/java/com/luxisoft/realityos/SocialAdministration.kt",
    "src/main/java/com/luxisoft/realityos/MediaViewer.kt",
    "src/main/java/com/luxisoft/realityos/MediaZoomPolicy.kt",
    "src/main/java/com/luxisoft/realityos/UnifiedSearch.kt",
    "src/test/java/com/luxisoft/realityos/MediaZoomPolicyTest.kt",
    "src/test/java/com/luxisoft/realityos/ChatHistoryTest.kt",
    "src/main/java/com/luxisoft/realityos/AiChat.kt",
    "src/main/java/com/luxisoft/realityos/RealityViewModel.kt",
    "src/main/java/com/luxisoft/realityos/RealityOsApp.kt",
    "src/main/java/com/luxisoft/realityos/ChatModels.kt",
    "src/main/java/com/luxisoft/realityos/ChatHistory.kt",
    fileTree("src/main/java/com/luxisoft/realityos/host") { include("**/*.kt") },
    fileTree("src/main/java/com/luxisoft/realityos/chat") { include("**/*.kt") },
)

tasks.register<JavaExec>("ktlintCheck") {
    group = "verification"
    description = "Check formatting of the refactored host and chat modules."
    classpath = ktlint
    mainClass.set("com.pinterest.ktlint.Main")
    inputs.files(refactoredKotlin)
    args(refactoredKotlin.files.map { it.absolutePath })
}

tasks.register<JavaExec>("ktlintFormat") {
    group = "formatting"
    description = "Format refactored host and chat modules; excludes biometric UI."
    classpath = ktlint
    mainClass.set("com.pinterest.ktlint.Main")
    args("--format")
    args(refactoredKotlin.files.map { it.absolutePath })
}
