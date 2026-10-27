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

android {
  namespace = "com.luxisoft.realityos"
  compileSdk = 36

  defaultConfig {
    applicationId = "com.luxisoft.realityos"
    minSdk = 31
    targetSdk = 36
    versionCode = 1
    versionName = "0.1.0"
    // Without this, AGP falls back to the legacy InstrumentationTestRunner,
    // which does not discover AndroidJUnit4 MockDeviceKit tests.
    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    manifestPlaceholders["mwdat_application_id"] =
      localProperties.getProperty("mwdat_application_id", "0")
    manifestPlaceholders["mwdat_client_token"] =
      localProperties.getProperty("mwdat_client_token", "0")
  }

  buildFeatures { buildConfig = true }
  buildTypes {
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
  implementation(libs.androidx.activity.compose)
  implementation(platform(libs.androidx.compose.bom))
  implementation(libs.androidx.ui)
  implementation(libs.androidx.ui.graphics)
  implementation(libs.androidx.ui.tooling.preview)
  implementation(libs.androidx.material3)
  implementation(libs.androidx.lifecycle.runtime.compose)
  implementation(libs.androidx.lifecycle.viewmodel.compose)
  implementation(libs.androidx.security.crypto)
  implementation(libs.mwdat.core)
  implementation(libs.mwdat.camera)
  implementation(libs.mwdat.display)
  implementation(libs.mwdat.speech)
  testImplementation("junit:junit:4.13.2")
  androidTestImplementation("androidx.test.ext:junit:1.2.1")
  androidTestImplementation("androidx.test:runner:1.6.2")
  // Debug builds expose Meta's Developer Preview on a phone. Release builds
  // never package Mock Device Kit.
  debugImplementation(libs.mwdat.mockdevice)
  // Instrumentation uses the same official kit independently of the app's
  // Debug source set.
  androidTestImplementation(libs.mwdat.mockdevice)
  debugImplementation("androidx.compose.ui:ui-tooling")
}
